from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.schemas.schema import ErrorResponse
from app.core.logger import logger
from app.exceptions.exceptions import AppException

class ErrorMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            # Handle custom app exceptions
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(f"[{request_id}] APP EXCEPTION: {exc.detail}")
            error_response = ErrorResponse(
                status_code=exc.status_code,
                detail=exc.detail,
                error_type=exc.error_type
            )
            return JSONResponse(status_code=exc.status_code, content=error_response.dict())
        except Exception as exc:
            # Handle unexpected exceptions
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(f"[{request_id}] UNHANDLED EXCEPTION: {exc}")
            return JSONResponse(
                status_code=500,
                content={"status_code": 500, "detail": "Internal server error"}
            )