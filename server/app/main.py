from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.router import api_router
from .core.config import get_settings
from .core.context import RequestContextMiddleware
from .core.errors import register_exception_handlers
from .core.logging import configure_logging
from .infra.db import dispose_db, get_sessionmaker, init_db
from .modules.auth.service import ensure_seed
from .modules.dicts.service import ensure_seed_dicts
from .modules.jobs.service import ensure_seed_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_json)
    init_db()
    if settings.seed_admin:
        async with get_sessionmaker()() as session:
            await ensure_seed(session)
            await ensure_seed_dicts(session)
            await ensure_seed_jobs(session)
            await session.commit()
    yield
    await dispose_db()


def create_app() -> FastAPI:
    app = FastAPI(title="JobClaw API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
