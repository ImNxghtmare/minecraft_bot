"""
Модуль безопасности: аутентификация, пароли, JWT токены
"""
import hashlib
import hmac
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext

from app.core.config import settings

# Контекст для хэширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Более безопасно, но медленнее
)

class SimpleJWT:
    """
    Простая реализация JWT для разработки
    В продакшене лучше использовать python-jose
    """

    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        self.secret_key = (secret_key or settings.jwt_secret_key).encode()
        self.algorithm = algorithm

    def create_access_token(
            self,
            data: Dict[str, Any],
            expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создание JWT токена
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "type": "access"
        })

        return self._encode(to_encode)

    def _encode(self, payload: Dict[str, Any]) -> str:
        """
        Кодирование JWT токена
        """
        # Заголовок
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }

        # Кодируем header и payload
        encoded_header = self._base64url_encode(
            json.dumps(header, separators=(",", ":")).encode()
        )

        encoded_payload = self._base64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )

        # Создаем подпись
        message = f"{encoded_header}.{encoded_payload}".encode()
        signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).digest()

        encoded_signature = self._base64url_encode(signature)

        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Декодирование и проверка JWT токена
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid token format")

            encoded_header, encoded_payload, encoded_signature = parts

            # Проверяем подпись
            message = f"{encoded_header}.{encoded_payload}".encode()
            expected_signature = hmac.new(
                self.secret_key,
                message,
                hashlib.sha256
            ).digest()

            actual_signature = self._base64url_decode(encoded_signature)

            if not hmac.compare_digest(expected_signature, actual_signature):
                raise ValueError("Invalid signature")

            # Декодируем payload
            payload_json = self._base64url_decode(encoded_payload)
            payload = json.loads(payload_json)

            # Проверяем срок действия
            exp_timestamp = payload.get("exp")
            if exp_timestamp is None:
                raise ValueError("Token has no expiration")

            if datetime.utcnow().timestamp() > exp_timestamp:
                raise ValueError("Token expired")

            return payload

        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def _base64url_encode(self, data: bytes) -> str:
        """
        Base64URL кодирование
        """
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _base64url_decode(self, data: str) -> bytes:
        """
        Base64URL декодирование
        """
        # Добавляем padding если нужно
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding

        return base64.urlsafe_b64decode(data)

# Глобальный экземпляр JWT
jwt_manager = SimpleJWT()

# Функции для работы с паролями
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Хэширование пароля
    """
    return pwd_context.hash(password)

def create_random_token(length: int = 32) -> str:
    """
    Создание случайного токена (для вебхуков и т.д.)
    """
    return secrets.token_urlsafe(length)

def create_verification_code(length: int = 6) -> str:
    """
    Создание кода подтверждения
    """
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))

# Функции для API ключей
def create_api_key() -> str:
    """
    Создание API ключа
    """
    prefix = "mc_"
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"

def hash_api_key(api_key: str) -> str:
    """
    Хэширование API ключа для хранения в БД
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

# Функции для проверки прав доступа
def check_permissions(user_role: str, required_role: str) -> bool:
    """
    Проверка прав доступа на основе ролей
    """
    role_hierarchy = {
        "admin": 3,
        "support": 2,
        "moderator": 1,
        "user": 0
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level

# Функции для валидации данных
def sanitize_input(text: str, max_length: int = 5000) -> str:
    """
    Очистка пользовательского ввода
    """
    if not text:
        return ""

    # Обрезаем до максимальной длины
    text = text[:max_length]

    # Удаляем опасные HTML теги (простая защита от XSS)
    import re
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<.*?javascript:.*?>', '', text, flags=re.IGNORECASE)

    # Экранируем специальные символы
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')

    return text.strip()

def is_valid_email(email: str) -> bool:
    """
    Проверка валидности email
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    """
    Проверка валидности номера телефона
    """
    import re
    # Простая проверка для российских номеров
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(pattern, phone))

# Функции для rate limiting (простая реализация)
class RateLimiter:
    """
    Простой rate limiter для защиты от спама
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_cache = {}

    async def check_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Проверка лимита запросов
        """
        current_time = datetime.utcnow().timestamp()
        window_start = current_time - window

        if self.redis:
            # Используем Redis если доступен
            try:
                # Удаляем старые записи
                await self.redis.zremrangebyscore(key, 0, window_start)

                # Считаем количество запросов в окне
                count = await self.redis.zcard(key)

                if count >= limit:
                    return False

                # Добавляем текущий запрос
                await self.redis.zadd(key, {str(current_time): current_time})
                await self.redis.expire(key, window)

                return True
            except Exception:
                # Если Redis недоступен, fallback на локальный кэш
                pass

        # Локальный кэш (in-memory)
        if key not in self.local_cache:
            self.local_cache[key] = []

        # Удаляем старые записи
        self.local_cache[key] = [
            timestamp for timestamp in self.local_cache[key]
            if timestamp > window_start
        ]

        if len(self.local_cache[key]) >= limit:
            return False

        # Добавляем текущий запрос
        self.local_cache[key].append(current_time)

        # Очищаем старые ключи (чтобы не рос бесконечно)
        if len(self.local_cache) > 1000:
            # Удаляем самые старые ключи
            keys_to_remove = list(self.local_cache.keys())[:100]
            for k in keys_to_remove:
                del self.local_cache[k]

        return True

# Создаем глобальный rate limiter
rate_limiter = RateLimiter()

# Функции для работы с сессиями
def create_session_id() -> str:
    """
    Создание ID сессии
    """
    return secrets.token_urlsafe(32)

def validate_session(session_id: str) -> bool:
    """
    Простая валидация сессии (в реальном приложении нужно проверять в БД)
    """
    if not session_id or len(session_id) < 32:
        return False
    return True

# Экспортируем основные функции
__all__ = [
    'jwt_manager',
    'verify_password',
    'get_password_hash',
    'create_random_token',
    'create_verification_code',
    'create_api_key',
    'hash_api_key',
    'check_permissions',
    'sanitize_input',
    'is_valid_email',
    'is_valid_phone',
    'rate_limiter',
    'create_session_id',
    'validate_session',
]