import asyncio
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class MessageQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing = False

    async def put(self, item: Tuple[str, dict]):
        """Добавление сообщения в очередь"""
        await self.queue.put(item)
        logger.debug(f"Message added to queue: {item[0]}")

    async def get(self) -> Optional[Tuple[str, dict]]:
        """Получение сообщения из очереди"""
        try:
            return await self.queue.get()
        except asyncio.CancelledError:
            return None

    async def process_messages(self, processor):
        """Фоновая обработка сообщений из очереди"""
        self.processing = True

        while self.processing:
            try:
                item = await self.get()
                if item is None:
                    continue

                platform, data = item

                try:
                    await processor.process_incoming_message(platform, data)
                except Exception as e:
                    logger.error(f"Error processing queued message: {e}")

                self.queue.task_done()

            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """Остановка обработки очереди"""
        self.processing = False

# Глобальная очередь
message_queue = MessageQueue()