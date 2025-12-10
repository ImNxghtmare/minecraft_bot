from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import uvicorn

app = FastAPI(
    title="Minecraft Support Bot",
    version="1.0.0",
    description="API для технической поддержки Minecraft сервера"
)

# SQLite база данных для начала
DB_FILE = "minecraft_bot.db"

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        platform_id TEXT NOT NULL,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT "open",
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ База данных создана: {DB_FILE}")

# Модели
class UserCreate(BaseModel):
    platform: str
    platform_id: str
    username: Optional[str] = None

class TicketCreate(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "Minecraft Support Bot API",
        "status": "running",
        "database": "SQLite",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

@app.post("/api/users")
async def create_user(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (platform, platform_id, username) VALUES (?, ?, ?)",
        (user.platform, user.platform_id, user.username)
    )

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "User created",
        "user_id": user_id,
        "platform": user.platform
    }

@app.get("/api/users")
async def get_users():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        "users": users,
        "count": len(users),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/tickets")
async def create_ticket(ticket: TicketCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tickets (user_id, title, description) VALUES (?, ?, ?)",
        (ticket.user_id, ticket.title, ticket.description)
    )

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "Ticket created",
        "ticket_id": ticket_id,
        "title": ticket.title,
        "status": "open"
    }

@app.get("/api/tickets")
async def get_tickets():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    tickets = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        "tickets": tickets,
        "count": len(tickets),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets")
    tickets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
    open_tickets = cursor.fetchone()[0]

    conn.close()

    return {
        "users": users,
        "tickets": tickets,
        "open_tickets": open_tickets,
        "database": "SQLite",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Инициализируем базу данных
    init_db()

    print("=" * 60)
    print("🤖 MINECRAFT SUPPORT BOT")
    print("=" * 60)
    print("\n🚀 Сервер запущен:")
    print("   📚 Документация: http://localhost:8000/docs")
    print("   🏠 Главная: http://localhost:8000/")
    print("\n🔧 Доступные эндпоинты:")
    print("   POST /api/users    - Создать пользователя")
    print("   GET  /api/users    - Получить пользователей")
    print("   POST /api/tickets  - Создать тикет")
    print("   GET  /api/tickets  - Получить тикеты")
    print("   GET  /api/stats    - Статистика")
    print("\n👤 Для будущей аутентификации:")
    print("   Email: admin@minecraft.local")
    print("   Пароль: Admin123!")
    print("\n" + "=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")