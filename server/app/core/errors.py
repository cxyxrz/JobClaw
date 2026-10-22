import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .response import ApiResponse

log = structlog.get_logger()


class AppError(Exception):
    code: int = 50000
    status_code: int = 500
    message: str = "internal error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: int | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class Unauthorized(AppError):
    code = 40100
    status_code = 401
    message = "unauthorized"


class Forbidden(AppError):
    code = 40300
    status_code = 403
    message = "forbidden"


class NotFound(AppError):
    code = 40400
    status_code = 404
    message = "not found"


class Conflict(AppError):
    code = 40900
    status_code = 409
    message = "conflict"


def _payload(code: int, message: str, data=None) -> dict:
    return ApiResponse(code=code, message=message, data=data).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def on_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            log.error("app_error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=exc.status_code, content=_payload(exc.code, exc.message)
        )

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_payload(40000, "validation error", jsonable_encoder(exc.errors())),
        )

    @app.exception_handler(StarletteHTTPException)
    async def on_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.status_code * 100, str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def on_unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error")
        return JSONResponse(status_code=500, content=_payload(50000, "internal error"))
