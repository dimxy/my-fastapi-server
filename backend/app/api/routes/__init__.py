from fastapi import APIRouter

from app.api.routes import users, llm_api

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(llm_api.router)
