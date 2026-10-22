from fastapi import APIRouter

from .v1 import admin, auth, dicts, jobs

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(dicts.router)
api_router.include_router(admin.router)
