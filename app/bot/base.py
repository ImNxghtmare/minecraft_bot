from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.user import PlatformType
from app.schemas.message import MessageCreate
from app.schemas.attachment import AttachmentCreate

class BaseBot(ABC):
    def __init__(self, platform: PlatformType):
        self.platform = platform

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def send_message(self, user_id: str, text: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def process_message(self, data: Dict[str, Any]) -> MessageCreate:
        pass

    @abstractmethod
    async def extract_attachments(self, data: Dict[str, Any]) -> list[AttachmentCreate]:
        pass