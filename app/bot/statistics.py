from app.bot.memory import USER_MEMORY

def get_user_stats(user_id: int) -> str:
    mem = USER_MEMORY.get(user_id)
    if not mem:
        return "Статистика пока отсутствует."

    return (
        f"📊 <b>Твоя статистика:</b>\n"
        f"Сообщений: <b>{mem['messages']}</b>\n"
        f"Токсичности: <b>{mem['toxicity']}</b>\n"
        f"Флуд: <b>{mem['flood']}</b>\n"
        f"Последний интент: <b>{mem['last_intent']}</b>\n"
        f"История: {len(mem['history'])} сообщений\n"
    )
