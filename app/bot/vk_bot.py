from aiohttp import web
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.bot.base import BaseBot
from app.core.config import settings
from app.models.user import PlatformType
from app.schemas.message import MessageCreate, MessageDirection
from app.schemas.attachment import AttachmentCreate
from app.models.message import AttachmentType

logger = logging.getLogger(__name__)

class VKBot(BaseBot):
    def __init__(self):
        super().__init__(PlatformType.VK)
        self.app = None
        self.secret_key = settings.vk_secret_key
        self.confirmation_code = settings.vk_confirmation_code
        self.group_id = settings.vk_group_id

    async def start(self):
        if not all([settings.vk_bot_token, settings.vk_group_id, settings.vk_confirmation_code]):
            logger.warning("VK bot configuration incomplete")
            return

        self.app = web.Application()
        self._setup_routes()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8081)
        await site.start()

        logger.info("VK bot started on port 8081")
        return self.app

    async def stop(self):
        if self.app:
            await self.app.shutdown()
            await self.app.cleanup()

    def _setup_routes(self):
        self.app.router.add_post('/vk/callback', self._handle_callback)
        self.app.router.add_get('/vk/callback', self._handle_verification)

    async def _handle_verification(self, request):
        """Обработка верификации Callback API"""
        params = request.query

        if params.get('group_id') == str(self.group_id):
            if params.get('type') == 'confirmation':
                return web.Response(text=self.confirmation_code)

        return web.Response(text='ok')

    async def _handle_callback(self, request):
        """Основной обработчик Callback API"""
        try:
            # Проверяем подпись
            if self.secret_key:
                body = await request.read()
                signature = request.headers.get('X-Signature', '')

                if not self._verify_signature(body, signature):
                    logger.warning("Invalid signature")
                    return web.Response(text='invalid signature', status=403)

                data = json.loads(body.decode('utf-8'))
            else:
                data = await request.json()

            # Обрабатываем событие
            event_type = data.get('type')

            if event_type == 'confirmation':
                return web.Response(text=self.confirmation_code)

            elif event_type == 'message_new':
                await self._handle_new_message(data['object']['message'])

            return web.Response(text='ok')

        except Exception as e:
            logger.error(f"Error processing callback: {e}")
            return web.Response(text='error', status=500)

    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Проверяет подпись VK"""
        if not self.secret_key:
            return True

        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, f"sha256={expected_signature}")

    async def _handle_new_message(self, message_data: Dict[str, Any]):
        """Обработка нового сообщения"""
        logger.info(f"Received VK message: {message_data}")

        # Добавляем в очередь для обработки
        from app.core.queue import message_queue
        await message_queue.put(("vk", message_data))

    async def send_message(self, user_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """Отправка сообщения через VK API"""
        import aiohttp

        params = {
            'user_id': user_id,
            'message': text,
            'random_id': int(datetime.now().timestamp() * 1000),
            'access_token': settings.vk_bot_token,
            'v': '5.199'
        }

        # Добавляем дополнительные параметры
        if 'keyboard' in kwargs:
            params['keyboard'] = json.dumps(kwargs['keyboard'])

        if 'attachment' in kwargs:
            params['attachment'] = kwargs['attachment']

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        'https://api.vk.com/method/messages.send',
                        params=params
                ) as response:
                    result = await response.json()

                    if 'error' in result:
                        logger.error(f"VK API error: {result['error']}")
                        return {
                            "success": False,
                            "error": result['error']
                        }

                    return {
                        "success": True,
                        "message_id": str(result['response']),
                        "result": result
                    }

        except Exception as e:
            logger.error(f"Error sending VK message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def process_message(self, data: Dict[str, Any]) -> MessageCreate:
        """Преобразует данные VK в MessageCreate"""
        message = data.get('message', {})

        return MessageCreate(
            user_id=0,  # Будет заполнено позже
            ticket_id=None,
            direction=MessageDirection.INCOMING,
            content=message.get('text'),
            platform_message_id=str(message.get('id')),
            is_ai_response=False
        )

    async def extract_attachments(self, data: Dict[str, Any]) -> List[AttachmentCreate]:
        """Извлекает вложения из сообщения VK"""
        message = data.get('message', {})
        attachments_data = message.get('attachments', [])
        attachments = []

        for att in attachments_data:
            att_type = att.get('type')

            if att_type == 'photo':
                # Берем самую большую фотографию
                photo = att['photo']
                sizes = photo.get('sizes', [])
                if sizes:
                    largest = max(sizes, key=lambda x: x.get('width', 0) * x.get('height', 0))
                    attachments.append(AttachmentCreate(
                        message_id=0,
                        attachment_type=AttachmentType.PHOTO,
                        file_id=str(photo.get('id')),
                        file_url=largest.get('url'),
                        file_size=None,
                        caption=None
                    ))

            elif att_type == 'doc':
                doc = att['doc']
                attachments.append(AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.DOCUMENT,
                    file_id=str(doc.get('id')),
                    file_url=doc.get('url'),
                    file_size=doc.get('size'),
                    mime_type=doc.get('ext'),
                    caption=doc.get('title')
                ))

            elif att_type == 'audio':
                audio = att['audio']
                attachments.append(AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.AUDIO,
                    file_id=str(audio.get('id')),
                    file_url=audio.get('url'),
                    file_size=None,
                    mime_type='mp3',
                    caption=f"{audio.get('artist')} - {audio.get('title')}"
                ))

            elif att_type == 'video':
                video = att['video']
                attachments.append(AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.VIDEO,
                    file_id=str(video.get('id')),
                    file_url=f"https://vk.com/video{video.get('owner_id')}_{video.get('id')}",
                    file_size=None,
                    caption=video.get('title')
                ))

            elif att_type == 'sticker':
                sticker = att['sticker']
                # VK стикеры обычно в нескольких размерах
                images = sticker.get('images', [])
                if images:
                    largest = max(images, key=lambda x: x.get('width', 0))
                    attachments.append(AttachmentCreate(
                        message_id=0,
                        attachment_type=AttachmentType.STICKER,
                        file_id=str(sticker.get('sticker_id')),
                        file_url=largest.get('url'),
                        file_size=None,
                        mime_type='png'
                    ))

        return attachments