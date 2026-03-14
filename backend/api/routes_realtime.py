import json
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/realtime", tags=["realtime"])

@router.post("/session")
async def create_realtime_session(request: Request):
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    offer_sdp = (await request.body()).decode("utf-8")
    if not offer_sdp.strip():
        raise HTTPException(status_code=400, detail="SDP offer is required")

    session = {
        "type": "realtime",
        "model": settings.openai_realtime_model,
        "instructions": "You are a helpful cooking assistant.",
        "audio": {
            "output": {
                "voice": settings.openai_realtime_voice,
            }
        },
    }

    # session must be a plain form field (no Content-Type header) so OpenAI's
    # multipart parser can find the sdp field that follows it.
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/realtime/calls",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            data={"session": json.dumps(session)},
            files={"sdp": ("offer.sdp", offer_sdp.encode("utf-8"), "application/sdp")},
        )

    if response.status_code >= 400:
        logger.error("OpenAI realtime error %s: %s", response.status_code, response.text)
        detail = response.text
        try:
            detail = response.json()
        except Exception:
            pass
        raise HTTPException(status_code=response.status_code, detail=detail)

    return PlainTextResponse(response.text, media_type="application/sdp")
