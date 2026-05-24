import logging
import os
import uuid
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.database import get_db
from backend.models import BillResponse, CreateBillRequest, PlayerResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def _push_bill_card(group_id: str, bill_id: str, bill_name: str, total: float,
                    computed: list[dict]) -> None:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    mini_app_id = os.environ.get("MINI_APP_ID", "")
    if not token:
        logger.error("PUSH SKIPPED: LINE_CHANNEL_ACCESS_TOKEN is not set")
        return
    if not mini_app_id:
        logger.error("PUSH SKIPPED: MINI_APP_ID is not set")
        return

    view_url = f"https://miniapp.line.me/{mini_app_id}/bill/{bill_id}"
    display_name = bill_name or "Badminton Bill"

    # Build player rows (cap at 8 to keep the card compact)
    MAX_ROWS = 8
    player_rows = []
    for p in computed[:MAX_ROWS]:
        player_rows.append({
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "contents": [
                {"type": "text", "text": p["name"], "size": "sm",
                 "color": "#374151", "flex": 1, "wrap": True},
                {"type": "text", "text": f"฿{p['amount']:,.2f}", "size": "sm",
                 "weight": "bold", "color": "#16a34a", "align": "end"},
            ],
        })
    if len(computed) > MAX_ROWS:
        player_rows.append({
            "type": "text",
            "text": f"…and {len(computed) - MAX_ROWS} more",
            "size": "xs", "color": "#9ca3af",
        })

    flex = {
        "type": "flex",
        "altText": f"🏸 {display_name} — ฿{total:,.2f}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#16a34a", "paddingAll": "16px",
                "contents": [
                    {"type": "text", "text": "🏸 New Bill", "size": "xs",
                     "color": "#bbf7d0"},
                    {"type": "text", "text": display_name, "size": "lg",
                     "weight": "bold", "color": "#ffffff", "wrap": True},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "box", "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "Total",
                             "size": "sm", "color": "#6b7280", "flex": 1},
                            {"type": "text", "text": f"฿{total:,.2f}",
                             "size": "sm", "weight": "bold", "color": "#16a34a",
                             "align": "end"},
                        ],
                    },
                    {"type": "separator", "margin": "sm"},
                    *player_rows,
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical", "paddingAll": "12px",
                "contents": [
                    {
                        "type": "button", "style": "primary", "color": "#22c55e",
                        "action": {"type": "uri", "label": "View My Share",
                                   "uri": view_url},
                    }
                ],
            },
        },
    }

    logger.info("PUSH attempting to group_id=%r bill_id=%s", group_id, bill_id)
    try:
        with httpx.Client(timeout=10) as client:
            res = client.post(
                LINE_PUSH_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={"to": group_id, "messages": [flex]},
            )
        if res.status_code == 200:
            logger.info("PUSH success bill_id=%s", bill_id)
        else:
            logger.error("PUSH failed status=%s body=%s", res.status_code, res.text)
    except Exception as e:
        logger.exception("PUSH exception bill_id=%s: %s", bill_id, e)


@router.post("/bills", response_model=dict)
def create_bill(req: CreateBillRequest, background_tasks: BackgroundTasks):
    if req.total_cost <= 0:
        raise HTTPException(status_code=400, detail="total_cost must be positive")
    if not req.players:
        raise HTTPException(status_code=400, detail="At least one player required")
    if req.split_mode not in ("equal", "hours"):
        raise HTTPException(status_code=400, detail="split_mode must be 'equal' or 'hours'")

    if req.split_mode == "hours":
        total_hours = sum(p.hours or 0 for p in req.players)
        if total_hours <= 0:
            raise HTTPException(status_code=400, detail="Total hours must be greater than 0")

    bill_id = uuid.uuid4().hex[:8]

    if req.split_mode == "equal":
        per_person = req.total_cost / len(req.players)
        computed = [
            {"name": p.name, "hours": None, "amount": round(per_person, 2)}
            for p in req.players
        ]
    else:
        total_hours = sum(p.hours or 0 for p in req.players)
        per_hour = req.total_cost / total_hours
        computed = [
            {"name": p.name, "hours": p.hours, "amount": round((p.hours or 0) * per_hour, 2)}
            for p in req.players
        ]

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO bills VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                bill_id,
                req.total_cost,
                req.court_name,
                req.note,
                req.split_mode,
                req.host_name,
                datetime.now(timezone.utc).isoformat(),
                req.session_hours,
                req.bank_account,
            ),
        )
        for p in computed:
            conn.execute(
                "INSERT INTO bill_players (bill_id, name, hours, amount) VALUES (?, ?, ?, ?)",
                (bill_id, p["name"], p["hours"], p["amount"]),
            )
        conn.commit()
    finally:
        conn.close()

    if req.group_id:
        background_tasks.add_task(
            _push_bill_card,
            req.group_id,
            bill_id,
            req.court_name or "",
            req.total_cost,
            computed,
        )
    else:
        logger.warning("PUSH SKIPPED: no group_id in request for bill_id=%s", bill_id)

    return {"id": bill_id}


@router.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: str):
    conn = get_db()
    try:
        bill = conn.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        players = conn.execute(
            "SELECT * FROM bill_players WHERE bill_id = ? ORDER BY id", (bill_id,)
        ).fetchall()
    finally:
        conn.close()

    return BillResponse(
        id=bill["id"],
        total_cost=bill["total_cost"],
        court_name=bill["court_name"],
        note=bill["note"],
        split_mode=bill["split_mode"],
        host_name=bill["host_name"],
        created_at=bill["created_at"],
        session_hours=bill["session_hours"],
        bank_account=bill["bank_account"],
        players=[
            PlayerResult(name=p["name"], hours=p["hours"], amount=p["amount"])
            for p in players
        ],
    )
