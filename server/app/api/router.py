from fastapi import APIRouter

from .v1 import agents, admin, auth, chat, collect, dicts, im, jobs

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(dicts.router)
api_router.include_router(collect.router)
api_router.include_router(admin.router)
api_router.include_router(chat.router)
api_router.include_router(im.router)
api_router.include_router(agents.router)
