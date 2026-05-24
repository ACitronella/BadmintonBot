import os
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    FlexMessage,
    FlexBubble,
    FlexBox,
    FlexText,
    FlexButton,
    URIAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

configuration = Configuration(access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""))
webhook_handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET", ""))

# Respond in groups only when these words appear (or bot is @mentioned)
_TRIGGERS = {"split", "bill", "แบ่ง", "บิล", "หาร", "คิดเงิน", "แบดมินตัน"}


def _should_respond(event: MessageEvent) -> bool:
    text = event.message.text.lower()
    if event.source.type == "user":
        return True  # always respond in 1-on-1
    # In groups: respond if bot was @mentioned OR a trigger word is present
    mentioned = bool(
        getattr(event.message, "mention", None)
        and event.message.mention.mentionees
    )
    return mentioned or any(w in text for w in _TRIGGERS)


def _bill_card(mini_app_url: str) -> FlexMessage:
    bubble = FlexBubble(
        body=FlexBox(
            layout="vertical",
            spacing="sm",
            contents=[
                FlexText(
                    text="🏸 Badminton Bill Splitter",
                    weight="bold",
                    size="lg",
                    color="#16a34a",
                ),
                FlexText(
                    text="Tap the button to create a new bill and split the court cost with your group.",
                    size="sm",
                    color="#6b7280",
                    wrap=True,
                ),
            ],
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                FlexButton(
                    style="primary",
                    color="#22c55e",
                    action=URIAction(label="Create New Bill", uri=mini_app_url),
                )
            ],
        ),
    )
    return FlexMessage(alt_text="🏸 Create a new badminton bill", contents=bubble)


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def on_text_message(event: MessageEvent) -> None:
    if not _should_respond(event):
        return

    mini_app_id = os.environ.get("MINI_APP_ID", "")
    if not mini_app_id:
        return  # Mini App not configured yet — stay silent

    mini_app_url = f"https://miniapp.line.me/{mini_app_id}"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[_bill_card(mini_app_url)],
            )
        )
