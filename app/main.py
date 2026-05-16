from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from app.models import *
from app.api.v1.routers import api_router   
from app.db.redis import connect_redis, disconnect_redis, check_redis
from app.db.session import AsyncSessionLocal
from app.seed.seed import seed_data
from app.core.config import settings
from app.core.rate_limit import ip_limiter
from app.core.logger import logger
from app.schemas.schema import ErrorResponse
from app.exceptions.exceptions import AppException
from app.services.storage import init_cloudinary
from app.websockets import (
    chat_handler,
    notification_handler,
    start_chat_pubsub_listener,
    start_notification_pubsub_listener,
)
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.middleware import (
    AuthMiddleware,
    LoggingMiddleware,
    ErrorMiddleware,
    setup_cors,
    
)
from app.middleware.cors_middleware import CORSMiddleware

# =============================================================================
# LIFESPAN
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting...")
    if settings.ENVIRONMENT == "development":
        async with AsyncSessionLocal() as db:
            await seed_data(db)

    await connect_redis()
    redis_ok = await check_redis()
    if redis_ok:
        logger.info("Redis connected successfully")
    else:
        logger.critical("Redis FAILED — rate limiting will not work!")

    init_cloudinary()
    logger.info("Cloudinary initialized")

    pubsub_task = asyncio.create_task(start_chat_pubsub_listener(chat_handler))
    chat_task = asyncio.create_task(start_notification_pubsub_listener(notification_handler))
    logger.info("WebSocket listeners started")

    yield

    logger.info("Server shutting down...")
    pubsub_task.cancel()
    chat_task.cancel()
    try:
        await asyncio.gather(pubsub_task, chat_task)
    except asyncio.CancelledError:
        pass
    await disconnect_redis()
    logger.info("Redis disconnected")

# =============================================================================
# APP
# =============================================================================
app = FastAPI(
    title="Backend App",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)


app.state.limiter = ip_limiter

# =============================================================================
# OPENAPI
# =============================================================================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    logger.warning(f"SECURITY | Rate limit hit | ip:{request.client.host} | path:{request.url.path}")
    return JSONResponse(
        status_code=429,
        content={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests.", "action": "WAIT_AND_RETRY"},
        headers={"Retry-After": "60"},
    )

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code,
            detail=exc.detail,
            error_type=exc.error_type,
        ).dict()
    )

# =============================================================================
# MIDDLEWARE
# =============================================================================
app.add_middleware(ErrorMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(SlowAPIMiddleware)
# setup_cors(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ROUTERS — ONE line ✅
# =============================================================================
app.include_router(api_router, prefix="/api/v1")

# =============================================================================
# HEALTH CHECK
# =============================================================================
@app.get("/", tags=["Health"])
async def root():
    return {"message": "Backend App is running"}