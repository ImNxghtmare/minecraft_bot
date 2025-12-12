from typing import Optional, List
from dataclasses import dataclass, field
import time


@dataclass
class UserContext:
    """
    Глобальный контекст пользователя:
    • FSM состояния (idle / waiting_close_confirm / unlink_confirm / etc)
    • последняя intent
    • режим оператора
    • флаг необходимости вызвать специалиста
    • история сообщений
    • буфер данных для многошаговых сценариев
    """

    # FSM состояние
    state: str = "idle"   # idle / waiting_close_confirm / other states...

    # последний распознанный интент
    last_intent: Optional[str] = None

    # пользователь сейчас в режиме с оператором?
    operator_mode: bool = False

    # нужно ли передать call_specialist = True в backend?
    need_specialist: bool = False

    # история сообщений (mini-LLM память)
    history: List[str] = field(default_factory=list)

    # временный буфер для многошаговых процессов
    data_buffer: dict = field(default_factory=dict)

    # время последней активности пользователя
    last_interaction: float = field(default_factory=time.time)

    # ============================================================
    #                   Х Е Л П Е Р Ы
    # ============================================================

    def push_history(self, text: str):
        """Добавляет текст в историю сообщений (до 20 элементов)."""
        self.history.append(text)
        if len(self.history) > 20:
            self.history.pop(0)

    def reset(self):
        """Полный сброс состояния в начальное (idle)."""
        self.state = "idle"
        self.last_intent = None
        self.operator_mode = False
        self.need_specialist = False
        self.history.clear()
        self.data_buffer.clear()
        self.last_interaction = time.time()
