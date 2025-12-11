from pydantic import BaseModel
from typing import Dict, Any

from app.api.v1.endpoints.auth import router


class IngestMessage(BaseModel):
    platform: str
    payload: Dict[str, Any]

@router.post("/ingest")
async def ingest_message(msg: IngestMessage):
    from app.core.queue import message_queue
    await message_queue.put((msg.platform, msg.payload))
    return {"status": "queued"}
