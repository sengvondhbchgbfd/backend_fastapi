# from fastapi import Request, status
# from fastapi.responses import JSONResponse
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.core.logger import logger


# class ErrorMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):
#         request_id = getattr(request.state, "request_id", "unknown")

#         try:
#             return await call_next(request)

#         except ValueError as e:
#             logger.warning(f"[{request_id}] ValueError: {e}")
#             return JSONResponse(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 content={"code": "VALIDATION_ERROR", "message": str(e)},
#             )

#         except PermissionError as e:
#             logger.warning(f"[{request_id}] PermissionError: {e}")
#             return JSONResponse(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 content={"code": "FORBIDDEN", "message": "No permission."},
#             )

#         except Exception as e:
#             # Full stack trace in error.log
#             logger.exception(
#                 f"[{request_id}] Unhandled error on "
#                 f"{request.method} {request.url.path} → {e}"
#             )
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content={
#                     "code":       "INTERNAL_ERROR",
#                     "message":    "Something went wrong.",
#                     "request_id": request_id,  # user can report this ID
#                 },
#             )

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.schemas.schema import ErrorResponse
from app.core.logger import logger
from app.core.exceptions import AppException

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