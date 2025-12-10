from fastapi import APIRouter
from app.api.v1.endpoints import auth, tickets, messages

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
# api_router.include_router(messages.router, prefix="/messages", tags=["messages"])