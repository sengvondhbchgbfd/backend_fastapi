# import time
# import uuid
# from fastapi import Request
# from starlette.middleware.base import BaseHTTPMiddleware
# from app.core.logger import logger


# class LoggingMiddleware(BaseHTTPMiddleware):

#     async def dispatch(self, request: Request, call_next):
#         request_id = str(uuid.uuid4())[:8]
#         start      = time.time()

#         # Attach request_id so other code can reference it
#         request.state.request_id = request_id

#         # ── Log incoming ───────────────────────────────────
#         logger.info(
#             f"[{request_id}] → {request.method} {request.url.path} "
#             f"| ip:{request.client.host} "
#             f"| ua:{request.headers.get('user-agent', 'unknown')[:40]}"
#         )

#         # ── Process ────────────────────────────────────────
#         response = await call_next(request)

#         # ── Log outgoing ───────────────────────────────────
#         duration = round((time.time() - start) * 1000, 2)
#         level    = "INFO" if response.status_code < 400 else "WARNING"

#         # logger.log(
#         #     level,
#         #     f"[{request_id}] ← {response.status_code} "
#         #     f"| {request.method} {request.url.path} "
#         #     f"| {duration}ms"
#         # )

#         logger.log(
#         level,
#         f"[{request_id}] ← {response.status_code} | {request.method} {request.url.path} | {duration}ms"
#         )

#         response.headers["X-Request-ID"] = request_id
#         return response
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger
import time, uuid

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        request.state.request_id = request_id

        # Log incoming request
        logger.info(f"[{request_id}] → {request.method} {request.url.path} | ip:{request.client.host}")

        # Call the next middleware / route
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = round((time.time() - start) * 1000, 2)
            logger.exception(f"[{request_id}] ERROR {request.method} {request.url.path} | {duration}ms")
            raise exc

        # Log outgoing response
        duration = round((time.time() - start) * 1000, 2)
        level = "INFO" if response.status_code < 400 else "WARNING"
        logger.log(level, f"[{request_id}] ← {response.status_code} {request.method} {request.url.path} | {duration}ms")

        # Attach request ID header
        response.headers["X-Request-ID"] = request_id

        return response