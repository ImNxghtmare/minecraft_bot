import logging
from logging.handlers import RotatingFileHandler

from app.core.config import settings

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

handler = RotatingFileHandler(
    "logs/app.log", maxBytes=10_000_000, backupCount=5
)

handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger("minecraft_support")
