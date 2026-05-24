import os
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

from bot.handlers import handle_message

load_dotenv()

app = FastAPI(title="Badminton Invoice Bot")

_channel_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
_channel_secret = os.environ["LINE_CHANNEL_SECRET"]

configuration = Configuration(access_token=_channel_token)
webhook_handler = WebhookHandler(_channel_secret)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "badminton-invoice-bot"}


@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        webhook_handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"status": "ok"}


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def on_text_message(event: MessageEvent):
    source = event.source
    if source.type == "group":
        source_id = f"group_{source.group_id}"
    elif source.type == "room":
        source_id = f"room_{source.room_id}"
    else:
        source_id = f"user_{source.user_id}"

    reply = handle_message(source_id, event.message.text)

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)],
            )
        )
