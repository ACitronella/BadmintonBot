import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.database import get_db

router = APIRouter(prefix="/api")

LINE_API = "https://api.line.me/v2/bot"


@router.get("/group/{group_id}/members")
async def get_group_members(group_id: str):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="LINE API not configured")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        # Fetch member IDs (first page, up to 100)
        ids_res = await client.get(
            f"{LINE_API}/group/{group_id}/members/ids",
            headers=headers,
        )
        if ids_res.status_code == 401:
            raise HTTPException(status_code=502, detail="Invalid LINE channel access token")
        if ids_res.status_code == 403:
            raise HTTPException(status_code=403, detail="Bot does not have permission to read this group")
        if ids_res.status_code == 404:
            raise HTTPException(status_code=404, detail="Group not found or bot is not in the group")
        if ids_res.status_code == 429:
            raise HTTPException(status_code=502, detail="LINE API rate limit exceeded, try again later")
        if ids_res.status_code != 200:
            raise HTTPException(status_code=502, detail=f"LINE API error: {ids_res.status_code}")

        member_ids: list[str] = ids_res.json().get("memberIds", [])

        # Fetch each member's profile
        members = []
        for user_id in member_ids:
            profile_res = await client.get(
                f"{LINE_API}/group/{group_id}/member/{user_id}",
                headers=headers,
            )
            if profile_res.status_code == 200:
                p = profile_res.json()
                members.append({
                    "userId": user_id,
                    "displayName": p.get("displayName", ""),
                    "pictureUrl": p.get("pictureUrl", ""),
                })

    return {"members": members}


@router.get("/user/{user_id}/group-id")
def get_user_group_id(user_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT group_id FROM user_group WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="No group found for this user. Make sure the bot is in the group and someone has sent a message.")
    return {"group_id": row["group_id"]}
