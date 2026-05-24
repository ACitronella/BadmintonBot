import os
import httpx
from fastapi import APIRouter, HTTPException

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
        if ids_res.status_code == 404:
            raise HTTPException(status_code=404, detail="Group not found or bot is not in the group")
        if ids_res.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch group member IDs")

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
