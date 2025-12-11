import abc
from app.models.user import PlatformType


class BaseBot(abc.ABC):
    """
    Базовый бот: Telegram / VK / Web.
    Processor вызывает методы этого класса.
    """

    def __init__(self, platform: PlatformType):
        self.platform = platform

    @abc.abstractmethod
    async def start(self):
        """Запуск бота (polling / webhook)"""
        pass

    @abc.abstractmethod
    async def stop(self):
        """Остановка бота"""
        pass

    # ===============================
    # Processor → Bot API
    # ===============================
    @abc.abstractmethod
    async def process_message(self, data: dict):
        """
        Получает raw-сообщение платформы и превращает его в MessageCreate.
        Processor вызывает это.
        """
        pass

    @abc.abstractmethod
    async def extract_attachments(self, data: dict):
        """
        Получает raw-сообщение платформы и возвращает list[AttachmentCreate]
        """
        pass

    # ===============================
    # Bot → User API
    # ===============================
    @abc.abstractmethod
    async def send_message(self, user_id: str, text: str, **kwargs):
        """
        Отправка сообщения пользователю (Telegram/VK)
        """
        pass
