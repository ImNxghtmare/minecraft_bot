import re
from typing import Dict, List, Tuple, Optional

import numpy as np
import faiss
from rapidfuzz import fuzz

# ======================================================
#  НАСТРОЙКИ ЭМБЕДДИНГОВ
# ======================================================

EMB_DIM = 256  # оптимальное значение для hash-embedding


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _embed(text: str) -> np.ndarray:
    """
    Простой, но быстрый hash-bag-of-words embedding.
    """
    text = _normalize(text)
    tokens = re.findall(r"[a-zа-я0-9]+", text)
    vec = np.zeros(EMB_DIM, dtype="float32")

    for tok in tokens:
        h = hash(tok) % EMB_DIM
        vec[h] += 1.0

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm

    return vec


# ======================================================
#  ГЛОБАЛЬНОЕ ЗНАНИЕ (FAQ → mini-LLM)
# ======================================================

_KNOWLEDGE_ITEMS: List[Tuple[str, str]] = [
    ("как дела", "Работаю как всегда 🤖💪"),
    ("ты кто", "Я бот поддержки CubeWorld, всегда на связи 😊"),
    ("что можешь", "Помогаю с поддержкой, платежами и отвечаю на вопросы 😎"),
    ("помоги", "Конечно, бро! Рассказывай, что случилось?"),
    ("привет", "Привет-привет! 👋 Чем помочь?"),
    ("здрасте", "Приветствую 👋 Что случилось?"),
    ("здравствуйте", "Здравствуйте! 👋 Как я могу помочь?"),
]

_KB_VECS = np.stack([_embed(q) for q, _ in _KNOWLEDGE_ITEMS])
_KB_INDEX = faiss.IndexFlatIP(EMB_DIM)
_KB_INDEX.add(_KB_VECS)


# ======================================================
#  ИНДИВИДУАЛЬНАЯ ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ
# ======================================================

class UserMemory:
    """
    Личная FAISS-память пользователя.
    """

    def __init__(self):
        self.index = faiss.IndexFlatIP(EMB_DIM)
        self.texts: List[str] = []
        self.vectors: List[np.ndarray] = []

    def add(self, text: str):
        vec = _embed(text)
        self.texts.append(text)
        self.vectors.append(vec)
        self.index.add(vec.reshape(1, -1))

    def search(self, text: str, top_k=3) -> List[Tuple[str, float]]:
        if not self.texts:
            return []
        q = _embed(text).reshape(1, -1)
        scores, idxs = self.index.search(q, min(top_k, len(self.texts)))
        out = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx >= 0:
                out.append((self.texts[idx], float(score)))
        return out


_USER_MEMORIES: Dict[int, UserMemory] = {}


def _get_user_memory(uid: int) -> UserMemory:
    if uid not in _USER_MEMORIES:
        _USER_MEMORIES[uid] = UserMemory()
    return _USER_MEMORIES[uid]


# ======================================================
#  λ-ROUTER — объединение нескольких сигналов
# ======================================================

def _router_score(mem: float, kb: float, hist: float) -> float:
    """
    λ-router комбинирует сигналы в финальную уверенность.
    Можно настраивать веса.
    """
    return (
            0.5 * kb +    # глобальное знание (FAQ)
            0.3 * mem +   # личная память
            0.2 * hist    # похожесть на прошлый текст
    )


# ======================================================
#  ОСНОВНОЙ mini-LLM
# ======================================================

def mini_llm_answer(
        user_id: int,
        history: List[str],
        text: str,
) -> Optional[str]:

    text_norm = _normalize(text)
    if not text_norm:
        return None

    # слишком короткие сообщения — не тратим мини-LLM
    if len(text_norm) < 3:
        return None

    # анти-спам внутри mini-LLM
    if len(text_norm.split()) > 20:  # слишком длинная простыня = оператор
        return None

    mem = _get_user_memory(user_id)

    # ----------------------------- 1) ЛИЧНАЯ ПАМЯТЬ -----------------------------
    mem_score = 0.0
    mem_text = None
    similar = mem.search(text_norm, top_k=1)
    if similar:
        mem_text, mem_score = similar[0]

    # ----------------------------- 2) ГЛОБАЛЬНОЕ Q/A -----------------------------
    q_vec = _embed(text_norm).reshape(1, -1)
    kb_scores, kb_idxs = _KB_INDEX.search(q_vec, 1)
    kb_score = float(kb_scores[0][0])
    kb_idx = int(kb_idxs[0][0]) if kb_idxs[0][0] >= 0 else -1

    # ----------------------------- 3) HISTORY MATCH ------------------------------
    hist_score = 0.0
    if history:
        last = _normalize(history[-1])
        hist_score = fuzz.partial_ratio(last, text_norm) / 100.0

    # ----------------------------- 4) λ-router ----------------------------------
    lam = _router_score(mem_score, kb_score, hist_score)

    # Записываем текст в память всегда
    mem.add(text_norm)

    # Модель недостаточно уверена → отдаём оператору
    if lam < 0.75:
        return None

    # ----------------------------- 5) ВЫБОР ОТВЕТА ------------------------------

    # A) пользователь уже спрашивал то же самое
    if mem_score >= 0.93:
        return (
            "🧠 Я помню, ты уже писал:\n"
            f"«{mem_text}»\n\n"
            "Если что-то изменилось — уточни детали 😉"
        )

    # B) попали в FAQ
    if kb_idx >= 0 and kb_score >= 0.82:
        _, answer = _KNOWLEDGE_ITEMS[kb_idx]
        return answer

    # C) продолжаем прошлый диалог
    if hist_score >= 0.85:
        return "Понял тебя, продолжаем. Что ещё уточнить? 🙂"

    # fallback на случай глупых срабатываний
    return None
