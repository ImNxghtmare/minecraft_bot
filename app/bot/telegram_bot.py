# app/bot/telegram_bot.py

import logging
import time
import re
from typing import List, Dict, Optional

from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message,
    PhotoSize,
    Document,
    Audio,
    Voice,
    Video,
    Sticker,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.enums import ParseMode
from aiogram.filters import Command

from app.core.config import settings
from app.bot.base import BaseBot
from app.core.queue import message_queue
from app.models.user import PlatformType
from app.schemas.message import MessageCreate, MessageDirection
from app.schemas.attachment import AttachmentCreate
from app.models.attachment import AttachmentType

# INTENTS
from app.bot.intents import (
    detect_intent,
    INTENT_RULES,
    INTENT_MEDIA,
    INTENT_TEAM,
    INTENT_UNLINK,
    INTENT_TRANSFER_PRIV,
    INTENT_TRANSFER_BIND,
    INTENT_PASSWORD_RESET,
    INTENT_TOTP,
    INTENT_REFUND,
    INTENT_ITEM_TRANSFER,
    INTENT_PAYMENT_PROBLEM,
    INTENT_FORCE_BIND,
    INTENT_AGENT_INFO,
    INTENT_APPEAL,
    INTENT_WIPE,
    INTENT_NEWS,
    INTENT_IDIOTIC,
    INTENT_OPERATOR,
    INTENT_HACKED,
    INTENT_UNKNOWN,
)

# MINI LLM + FAISS MEMORY
from app.bot.mini_llm import mini_llm_answer

# КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ
from app.bot.context import UserContext

logger = logging.getLogger("telegram.bot")
router = Router()

# ======================================================
#  ГЛОБАЛЬНЫЕ СТРУКТУРЫ СОСТОЯНИЯ
# ======================================================

# антифлуд
USER_LAST_MESSAGE: Dict[int, float] = {}
USER_FLOOD_SCORE: Dict[int, int] = {}

# контексты (FSM + история + флаги)
USER_CONTEXTS: Dict[int, UserContext] = {}

FLOOD_WARNINGS = [
    "✋ Полегче, бро. Я всё вижу 😄",
    "🤚 Дай чуть подумать...",
    "🧠 Я не успеваю читать, ты слишком быстрый 💨",
]


def get_ctx(user_id: int) -> UserContext:
    """
    Достаём (или создаём) контекст пользователя.
    """
    ctx = USER_CONTEXTS.get(user_id)
    if ctx is None:
        ctx = UserContext()
        USER_CONTEXTS[user_id] = ctx
    ctx.last_interaction = time.time()
    return ctx


# ======================================================
#  ТОКСИЧНОСТЬ / АНТИФЛУД
# ======================================================

def is_toxic(text: str) -> bool:
    bad_words = [
        "бля",
        "сука",
        "пизд",
        "хуй",
        "еба",
        "нах",
        "уеб",
        "мраз",
        "пидор",
        "пидр",
        "еблан",
        "даун",
        "долбаеб",
        "долбоеб",
    ]
    t = (text or "").lower()
    return any(w in t for w in bad_words)


def toxic_reply() -> str:
    return (
        "🔥 Понимаю, эмоции — это сила 😅\n\n"
        "Давай спокойно: что случилось?"
    )


def check_flood(user_id: int) -> Optional[str]:
    """
    Простая модель анти-флуда.
    """
    now = time.time()
    last = USER_LAST_MESSAGE.get(user_id, 0.0)

    # чаще, чем раз в ~0.8 сек — подозрительно
    if now - last < 0.8:
        USER_FLOOD_SCORE[user_id] = USER_FLOOD_SCORE.get(user_id, 0) + 1
    else:
        USER_FLOOD_SCORE[user_id] = 0

    USER_LAST_MESSAGE[user_id] = now

    score = USER_FLOOD_SCORE[user_id]
    if score == 2:
        return FLOOD_WARNINGS[0]
    if score == 4:
        return FLOOD_WARNINGS[1]
    if score >= 6:
        return FLOOD_WARNINGS[2]

    return None


# ======================================================
#  КЛАВИАТУРЫ
# ======================================================

def kb_url(url: str, title: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=title, url=url)]]
    )


def kb_inline_operator() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Позвать оператора 👨‍💼",
                    callback_data="call_operator",
                )
            ]
        ]
    )


def kb_operator_panel() -> ReplyKeyboardMarkup:
    """
    Обычная (НЕ inline) клавиатура при работе с оператором.
    Теперь только одна кнопка — 'Закрыть обращение'.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Закрыть обращение")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def kb_close_confirm_panel() -> ReplyKeyboardMarkup:
    """
    Клавиатура для подтверждения закрытия тикета.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить")],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


KB_REMOVE = ReplyKeyboardRemove()


# ======================================================
#  ХЕЛПЕР: РЕГЕКС-ПРОВЕРКА ДАННЫХ ПО ОПЛАТЕ
# ======================================================

def looks_like_payment_data(msg: Message, text_lower: str) -> bool:
    """
    Эвристика: похоже ли сообщение на заполненную форму
    по "не пришёл донат / товар".
    """

    # ключевые слова по получателю
    has_nick = any(
        word in text_lower for word in ["получател", "ник", "никнейм", "клан"]
    )

    # дата вида 01.01.2025 или 01/01/2025
    has_datetime = bool(
        re.search(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b", text_lower)
    )

    # любой более-менее валидный email
    has_email = bool(
        re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_lower)
    )

    # прикреплённый PDF-документ
    has_pdf = bool(
        msg.document
        and msg.document.mime_type
        and "pdf" in msg.document.mime_type.lower()
    )

    signals = [has_nick, has_datetime, has_email, has_pdf]
    count_signals = sum(1 for s in signals if s)

    # Если есть PDF + хоть что-то ещё — уже достаточно убедительно
    if has_pdf and (has_email or has_datetime or has_nick):
        return True

    # Иначе хотим хотя бы 2 уверенных признака
    return count_signals >= 2


# ======================================================
#  АВТО-ОТВЕТЫ (до передачи в очередь)
# ======================================================

async def try_autoreply(bot: Bot, msg: Message):
    text = msg.text or msg.caption
    if not text:
        return

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    ctx = get_ctx(user_id)

    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    # Если уже вызвали оператора — не мешаем, просто молчим
    if ctx.operator_mode:
        return

    # ===== АНТИФЛУД =====
    flood_msg = check_flood(user_id)
    if flood_msg:
        await bot.send_message(chat_id, flood_msg)
        return

    # ===== ИСТОРИЯ =====
    ctx.push_history(text_stripped)
    history = ctx.history

    # ===== ТОКСИЧНОСТЬ =====
    if is_toxic(text_stripped):
        await bot.send_message(chat_id, toxic_reply())
        return

    # ===== INTENT DETECTION =====
    prev_intent = ctx.last_intent or INTENT_UNKNOWN
    intent = detect_intent(text_stripped)
    ctx.last_intent = intent

    # ===== ПОСТ-ФЛОУ ДЛЯ ОТВЯЗКИ АККАУНТА =====
    if prev_intent == INTENT_UNLINK and intent == INTENT_UNKNOWN:
        if "я согласен" in text_lower:
            ctx.operator_mode = True
            ctx.need_specialist = True
            ctx.state = "operator"
            await bot.send_message(
                chat_id,
                "✅ Принял согласие на отвязку аккаунта.\n"
                "Передаю запрос оператору, он продолжит с тобой диалог 👨‍💼",
                reply_markup=kb_operator_panel(),
            )
            return

    # ===== ПОСТ-ФЛОУ ДЛЯ ПРОБЛЕМЫ ОПЛАТЫ (не пришёл товар/донат) =====
    if prev_intent == INTENT_PAYMENT_PROBLEM and intent == INTENT_UNKNOWN:
        # проверяем, похоже ли сообщение на форму с данными
        if looks_like_payment_data(msg, text_lower):
            ctx.operator_mode = True
            ctx.need_specialist = True
            ctx.state = "operator"
            await bot.send_message(
                chat_id,
                "✅ Принял данные по оплате. Передаю их оператору.\n"
                "Он вернётся с ответом, как только проверит информацию 👨‍💼",
                reply_markup=kb_operator_panel(),
            )
            return

    # ===== ПОСТ-ФЛОУ ДЛЯ ВЗЛОМА (INTENT_HACKED) =====
    if prev_intent == INTENT_HACKED and intent == INTENT_UNKNOWN:
        # Пользователь описал проблему после предупреждения → зовём оператора
        ctx.operator_mode = True
        ctx.need_specialist = True
        ctx.state = "operator"
        await bot.send_message(
            chat_id,
            "📞 Подключаю оператора, чтобы детально проверить безопасность аккаунта.\n"
            "Он продолжит с тобой диалог в этом чате.",
            reply_markup=kb_operator_panel(),
        )
        return

    # =======================
    #  ОТВЕТЫ ПО ИНТЕНТАМ
    # =======================

    if intent == INTENT_RULES:
        await bot.send_message(
            chat_id,
            "📘 <b>Правила проекта</b>:\nhttps://vk.com/topic-213058175_49087108",
            reply_markup=kb_url(
                "https://vk.com/topic-213058175_49087108", "Открыть правила"
            ),
        )
        return

    if intent == INTENT_MEDIA:
        await bot.send_message(
            chat_id,
            "🎥 <b>Набор в Media:</b>\nhttps://vk.com/topic-213058175_48919352",
            reply_markup=kb_url(
                "https://vk.com/topic-213058175_48919352", "Открыть набор"
            ),
        )
        return

    if intent == INTENT_TEAM:
        await bot.send_message(
            chat_id,
            "👥 <b>Набор в Команду:</b>\nhttps://vk.com/topic-213058175_48975272",
            reply_markup=kb_url(
                "https://vk.com/topic-213058175_48975272", "Условия"
            ),
        )
        return

    if intent == INTENT_UNLINK:
        await bot.send_message(
            chat_id,
            "🔓 <b>Отвязка аккаунта</b>:\n"
            "Отмена привязки сопровождается <b>перманентной блокировкой</b> аккаунта.\n\n"
            "Если вы согласны на такой исход, напишите сюда:\n"
            "<i>я согласен на отмену привязки аккаунта ВАШНИК и его перманентную блокировку</i>.",
        )
        return

    if intent == INTENT_TRANSFER_PRIV:
        await bot.send_message(
            chat_id,
            "💎 <b>Перенос привилегии</b>\n"
            "Переносится только привилегия. Условия:\n"
            "• инициировать перенос может только владелец аккаунта;\n"
            "• оба аккаунта не должны иметь активных блокировок.\n"
            "Если всё подходит — сообщите оператору, он продолжит оформление.",
        )
        return

    if intent == INTENT_TRANSFER_BIND:
        await bot.send_message(
            chat_id,
            "🔗 <b>Перенос привязки аккаунта</b>\n"
            "Заполните форму: https://vk.cc/czfKhH",
            reply_markup=kb_url("https://vk.cc/czfKhH", "Открыть форму"),
        )
        return

    if intent == INTENT_PASSWORD_RESET:
        await bot.send_message(
            chat_id,
            "🔐 <b>Сброс / смена пароля</b>\n"
            "Нажмите кнопку <b>«Сброс пароля»</b> в панели бота VK.\n"
            "Если панели нет — отправьте команду <b>МоиАккаунты</b> "
            "и выберите нужный аккаунт.",
        )
        return

    if intent == INTENT_TOTP:
        await bot.send_message(
            chat_id,
            "🔑 <b>Инструкция по TOTP</b>:\nhttps://vk.com/@cubeworldpro-totp",
            reply_markup=kb_url(
                "https://vk.com/@cubeworldpro-totp", "Открыть инструкцию"
            ),
        )
        return

    if intent == INTENT_REFUND:
        await bot.send_message(
            chat_id,
            "💵 <b>Возврат средств</b>\n"
            "Нам нужны: получатель (ник/клан), товар, дата и время оплаты,\n"
            "адрес электронной почты и PDF-квитанция. Возврат возможен только,\n"
            "если товар ещё не был использован и с момента оплаты прошло не более 14 дней.",
        )
        return

    if intent == INTENT_ITEM_TRANSFER:
        await bot.send_message(
            chat_id,
            "📦 <b>Перенос товара</b>\n"
            "Если вы оплатили на неправильный аккаунт — напишите:\n"
            "1) На кого пришёл товар (ник/клан).\n"
            "2) На кого нужно перенести.\n"
            "3) Название товара и количество.\n"
            "4) Дата и время оплаты.\n"
            "5) Email и PDF-квитанция.\n\n"
            "Перенос возможен только если первичный получатель не успел им воспользоваться.",
        )
        return

    if intent == INTENT_PAYMENT_PROBLEM:
        await bot.send_message(
            chat_id,
            "🧾 <b>Не пришёл донат / товар</b>\n"
            "Для решения проблемы нам нужно получить от вас информацию:\n\n"
            "1. Получатель (игровой никнейм или название клана и т.п.), который был указан при оплате.\n"
            "2. Название товара и количество (если указывалось).\n"
            "3. Дата и время оплаты.\n"
            "4. Адрес электронной почты.\n"
            "5. Квитанция (справка, чек) об оплате в формате PDF.\n\n"
            "Квитанцию можно скачать из почты, указанной при оплате, либо в приложении/на сайте банка.\n"
            "Без квитанции проблему рассматривать не будем.\n\n"
            "Пример оформления:\n"
            "1. Получатель Agent\n"
            "2. Название товара и количество: Ellipse\n"
            "3. Дата и время оплаты: 01.01.2025 10:00 (МСК)\n"
            "4. Адрес электронной почты: support@cubeworld.pro\n"
            "5. Квитанция: приложенный PDF-файл.",
        )
        # дальше пользователь отправит данные → сработает блок prev_intent == INTENT_PAYMENT_PROBLEM
        return

    if intent == INTENT_FORCE_BIND:
        await bot.send_message(
            chat_id,
            "🔒 <b>Принудительная привязка</b>\n"
            "После выполнения привязки отправьте команду <b>/refresh</b> боту VK,\n"
            "чтобы аккаунт появился среди привязанных.",
        )
        return

    if intent == INTENT_AGENT_INFO:
        await bot.send_message(
            chat_id,
            "👨‍💼 <b>Агенты поддержки</b> — не высшая администрация.\n"
            "Они передают заявки наверх, и ожидание ответа может занимать до 48 часов.",
        )
        return

    if intent == INTENT_APPEAL:
        await bot.send_message(
            chat_id,
            "⚖️ <b>Обжалование блокировок / жалобы</b>\n"
            "Сообщество для апелляций: https://vk.com/cubeworldj",
            reply_markup=kb_url("https://vk.com/cubeworldj", "Перейти"),
        )
        return

    if intent == INTENT_WIPE:
        await bot.send_message(
            chat_id,
            "🗑 <b>Вайп</b>\n"
            "Точные дата и время вайпа заранее не сообщаются.\n"
            "Следите за новостями в основном сообществе и TG-канале проекта.",
        )
        return

    if intent == INTENT_NEWS:
        await bot.send_message(
            chat_id,
            "📰 <b>Новости проекта</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="VK",
                            url="https://vk.com/cubeworldpro",
                        ),
                        InlineKeyboardButton(
                            text="Telegram",
                            url="https://t.me/cubeworld_pro",
                        ),
                    ]
                ]
            ),
        )
        return

    if intent == INTENT_HACKED:
        ctx.operator_mode = True
        ctx.need_specialist = True
        ctx.state = "operator"

        await bot.send_message(
            chat_id,
            "🚨 <b>Похоже, ваш аккаунт могли скомпрометировать.</b>\n"
            "Срочно смените пароль и включите двухфакторную защиту.\n"
            "Опишите проблему подробнее, оператор поможет разобраться.",
            reply_markup=kb_operator_panel(),
        )
        return

    if intent == INTENT_IDIOTIC:
        await bot.send_message(chat_id, toxic_reply())
        return

    if intent == INTENT_OPERATOR:
        ctx.operator_mode = True
        ctx.need_specialist = True
        ctx.state = "operator"
        await bot.send_message(
            chat_id,
            "📞 Зову оператора. Он подключится, как только освободится.\n"
            "Пока что можешь дополнительно описать проблему.",
            reply_markup=kb_operator_panel(),
        )
        return

    # ===== ИНТЕНТ НЕ НАЙДЕН → mini-LLM (FAISS + память) =====
    answer = mini_llm_answer(user_id=user_id, history=history, text=text_stripped)
    if answer:
        await bot.send_message(chat_id, answer)
        return

    # ===== НИЧЕГО НЕ ПОНЯТО → inline-кнопка оператора =====
    await bot.send_message(
        chat_id,
        "🤔 Я не совсем понял запрос.\n"
        "Хочешь — позову оператора 👇",
        reply_markup=kb_inline_operator(),
    )


# ======================================================
#  HANDLERS
# ======================================================

@router.message(Command("start"))
async def handle_start(msg: Message):
    user_id = msg.from_user.id
    ctx = get_ctx(user_id)
    ctx.reset()

    await msg.answer(
        "👋 Привет! Я бот умной поддержки CubeWorld.\n"
        "Напиши свой вопрос — я попробую помочь.\n",
        reply_markup=KB_REMOVE,
    )

    # /start сам по себе не запускает try_autoreply, чтобы не ловить странные интенты
    await message_queue.put(("telegram", msg.model_dump()))


@router.message(Command("operator"))
async def handle_operator(msg: Message):
    user_id = msg.from_user.id
    ctx = get_ctx(user_id)
    ctx.operator_mode = True
    ctx.last_intent = INTENT_OPERATOR
    ctx.need_specialist = True
    ctx.state = "operator"

    await msg.answer(
        "📨 Оператор уведомлён. Опиши проблему как можно подробнее.",
        reply_markup=kb_operator_panel(),
    )
    data = msg.model_dump()
    data["call_specialist"] = True
    await message_queue.put(("telegram", data))


@router.message()
async def handle_all(msg: Message):
    user_id = msg.from_user.id
    ctx = get_ctx(user_id)
    text_raw = msg.text or msg.caption or ""
    text = text_raw.strip().lower()

    # --- двухшаговое закрытие обращения ---
    if ctx.state == "waiting_close_confirm":
        if text == "подтвердить":
            # реально закрываем тикет
            ctx.reset()
            await msg.answer(
                "✅ Обращение закрыто. Если что — напиши ещё раз.",
                reply_markup=ReplyKeyboardRemove(),
            )
            data = msg.model_dump()
            data["close_ticket"] = True
            await message_queue.put(("telegram", data))
            return
        elif text == "отмена":
            # отменяем закрытие, возвращаемся в оператор-режим
            ctx.state = "operator"
            ctx.operator_mode = True
            await msg.answer(
                "👌 Окей, обращение оставляю открытым.",
                reply_markup=kb_operator_panel(),
            )
            await message_queue.put(("telegram", msg.model_dump()))
            return
        # если что-то другое написал — просто игнорим это состояние дальше
        # и пускаем в обычный поток

    # --- кнопка "Закрыть обращение" (первый шаг) ---
    if text == "закрыть обращение":
        if ctx.operator_mode:
            ctx.state = "waiting_close_confirm"
            await msg.answer(
                "❓ Точно закрываем обращение?\n"
                "После закрытия продолжить диалог в этом тикете будет нельзя.",
                reply_markup=kb_close_confirm_panel(),
            )
            await message_queue.put(("telegram", msg.model_dump()))
            return
        # если не оператор-режим — просто игнорим или можно что-то ответить
        # но не закрываем тикет

    logger.info(f"[TG] message from {msg.from_user.id}: {msg.text!r}")

    # автоответ (если не оператор-режим / не флудаем / не токс)
    await try_autoreply(msg.bot, msg)

    # подготовка payload для очереди
    payload = msg.model_dump()

    # если во время try_autoreply мы решили, что нужен оператор
    if ctx.need_specialist:
        payload["call_specialist"] = True
        # сбросим флаг, чтобы не дублировать
        ctx.need_specialist = False

    await message_queue.put(("telegram", payload))


# ======================================================
#  BOT CLASS
# ======================================================

class TelegramBot(BaseBot):
    def __init__(self):
        super().__init__(PlatformType.TELEGRAM)
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None

    async def start(self):
        token = settings.telegram_bot_token
        if not token:
            logger.warning("Telegram token missing")
            return

        self.bot = Bot(
            token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        self.dp = Dispatcher()
        self.dp.include_router(router)

        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logger.warning(f"[TG] delete_webhook failed: {e!r}")

        logger.info("[TG] Starting POLLING…")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        if self.bot:
            await self.bot.session.close()

    async def process_message(self, data: dict) -> MessageCreate:
        msg = Message(**data)
        return MessageCreate(
            user_id=0,
            ticket_id=None,
            direction=MessageDirection.INCOMING,
            content=msg.text or msg.caption,
            platform_message_id=str(msg.message_id),
            is_ai_response=False,
        )

    async def send_message(self, user_id: str, text: str, **kwargs):
        """
        Отправка сообщения пользователю (реализация BaseBot).
        """
        if not self.bot:
            return {"success": False, "error": "Telegram bot is not running"}

        try:
            m = await self.bot.send_message(user_id, text, **kwargs)
            return {"success": True, "message_id": m.message_id}
        except Exception as e:
            logger.exception(f"[TG] send_message error: {e}")
            return {"success": False, "error": str(e)}

    async def extract_attachments(self, data: dict) -> List[AttachmentCreate]:
        msg = Message(**data)
        out: List[AttachmentCreate] = []

        if msg.photo:
            largest: PhotoSize = max(msg.photo, key=lambda p: p.file_size or 0)
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.PHOTO,
                    file_id=largest.file_id,
                    file_size=largest.file_size,
                    caption=msg.caption,
                )
            )

        if msg.document:
            d: Document = msg.document
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.DOCUMENT,
                    file_id=d.file_id,
                    mime_type=d.mime_type,
                    file_size=d.file_size,
                    caption=msg.caption,
                )
            )

        if msg.audio:
            a: Audio = msg.audio
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.AUDIO,
                    file_id=a.file_id,
                    mime_type=a.mime_type,
                    file_size=a.file_size,
                )
            )

        if msg.voice:
            v: Voice = msg.voice
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.VOICE,
                    file_id=v.file_id,
                    file_size=v.file_size,
                    mime_type=v.mime_type,
                )
            )

        if msg.video:
            v: Video = msg.video
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.VIDEO,
                    file_id=v.file_id,
                    mime_type=v.mime_type,
                    caption=msg.caption,
                )
            )

        if msg.sticker:
            s: Sticker = msg.sticker
            out.append(
                AttachmentCreate(
                    message_id=0,
                    attachment_type=AttachmentType.STICKER,
                    file_id=s.file_id,
                )
            )

        return out
