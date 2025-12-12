import time
from collections import defaultdict

# Храним в памяти (можно вынести в Redis позже)
USER_MEMORY = defaultdict(lambda: {
    "history": [],
    "last_intent": None,
    "toxicity": 0,
    "messages": 0,
    "flood": 0,
    "created_at": time.time(),
})

def update_memory(user_id: int, text: str, intent: str, toxic: bool, flood: bool):
    mem = USER_MEMORY[user_id]
    mem["messages"] += 1
    mem["last_intent"] = intent
    mem["history"].append(text)

    if toxic:
        mem["toxicity"] += 1
    if flood:
        mem["flood"] += 1

    # Ограничиваем историю
    if len(mem["history"]) > 20:
        mem["history"] = mem["history"][-20:]

def get_memory(user_id: int):
    return USER_MEMORY.get(user_id)
