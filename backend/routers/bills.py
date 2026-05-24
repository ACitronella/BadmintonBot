import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from backend.database import get_db
from backend.models import BillResponse, CreateBillRequest, PlayerResult

router = APIRouter(prefix="/api")


@router.post("/bills", response_model=dict)
def create_bill(req: CreateBillRequest):
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
            "INSERT INTO bills VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                bill_id,
                req.total_cost,
                req.court_name,
                req.note,
                req.split_mode,
                req.host_name,
                datetime.now(timezone.utc).isoformat(),
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
        players=[
            PlayerResult(name=p["name"], hours=p["hours"], amount=p["amount"])
            for p in players
        ],
    )
