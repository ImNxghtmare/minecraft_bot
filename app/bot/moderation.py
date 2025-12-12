import time
from rapidfuzz import fuzz


# ==========================
# АНТИ-ТОКСИК СЛОВАРЬ
# ==========================

TOXIC_WORDS = [
    "ебан", "еблан", "сука", "блять", "блядь", "нахуй",
    "пидор", "пидр", "хуй", "пизда", "мразь", "долбаеб",
    "идиот", "тупой", "тупица", "сдохни", "убью", "вы че конченые",
]

SOFT_WORDS = [
    "помоги", "пж", "пжж", "умоляю", "прошу",
    "не работает", "сломалось", "беда", "проблема",
    "пожалуйста", "не понимаю", "что делать"
]


# ==========================
# АНТИ-ФЛУД
# ==========================

USER_TIMERS = {}      # user_id -> last_message_timestamp
USER_FLOOD_COUNT = {} # user_id -> spam counter

FLOOD_INTERVAL = 1.2      # если пишет сообщения чаще чем раз в 1.2 сек → флуд
FLOOD_MAX = 4             # после 4 флуда подряд → мут на время
FLOOD_MUTE_TIME = 20      # время мута в сек


USER_MUTES = {}           # user_id -> mute_until_timestamp



def is_muted(user_id: int) -> bool:
    now = time.time()
    mute_until = USER_MUTES.get(user_id, 0)
    return now < mute_until



def register_message(user_id: int) -> str | None:
    """
    Возвращает:
      None → всё ок
      "mute" → чел в муте
      "flood" → предупреждение
      "muted_now" → его только что замутили
    """

    now = time.time()

    # проверяем, не в муте ли он
    if is_muted(user_id):
        return "mute"

    last = USER_TIMERS.get(user_id, 0)
    diff = now - last

    USER_TIMERS[user_id] = now

    # если пишет слишком часто → flood
    if diff < FLOOD_INTERVAL:
        USER_FLOOD_COUNT[user_id] = USER_FLOOD_COUNT.get(user_id, 0) + 1
    else:
        USER_FLOOD_COUNT[user_id] = 0

    if USER_FLOOD_COUNT[user_id] >= FLOOD_MAX:
        USER_MUTES[user_id] = now + FLOOD_MUTE_TIME
        USER_FLOOD_COUNT[user_id] = 0
        return "muted_now"

    if diff < FLOOD_INTERVAL:
        return "flood"

    return None


# ==========================
# ТОКСИЧНОСТЬ
# ==========================

def toxicity_level(text: str) -> int:
    """
    Возвращает число от 0 до 100 — уровень токсичности.
    """
    t = text.lower()
    score = 0

    for w in TOXIC_WORDS:
        if fuzz.partial_ratio(t, w) > 80:
            score += 25

    return min(score, 100)


def is_soft_text(text: str) -> bool:
    t = text.lower()
    for w in SOFT_WORDS:
        if fuzz.partial_ratio(t, w) > 70:
            return True
    return False


# ==========================
# МЕМЫ ДЛЯ ТОКСИКОВ 💀
# ==========================

MEMES = [
    "💀 Тебе бы маты на креатив пустить… а не на поддержку.",
    "🤡 Бро, токсичность — это не скилл.",
    "🧠 Звучишь, как человек, которому нужен вайп не на сервере, а в голове.",
    "🥲 Ну и зачем такие слова? Я же просто бот…",
    "😹 Расслабься, путник. Проблемы решатся без матов.",
]
