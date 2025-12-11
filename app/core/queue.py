import asyncio
import logging
from typing import Tuple, Optional

logger = logging.getLogger("queue")

class MessageQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self._running = False

    async def put(self, item: Tuple[str, dict]):
        """Добавить сообщение в очередь"""
        await self.queue.put(item)
        logger.debug(f"Queued message: {item}")

    async def get(self) -> Optional[Tuple[str, dict]]:
        try:
            return await self.queue.get()
        except asyncio.CancelledError:
            return None

    async def process_messages(self, processor):
        self._running = True
        while self._running:
            item = await self.get()
            if item is None:
                continue

            platform, data = item

            try:
                await processor.process(platform, data)
            except Exception as e:
                logger.error(f"Error processing queued message: {e}", exc_info=True)

            self.queue.task_done()

    def stop(self):
        self._running = False


message_queue = MessageQueue()
