from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.models import *
from app.routers.users_router          import router, role_router, department_router
from app.routers.auth_router           import router as auth_router
from app.db.redis                      import connect_redis, disconnect_redis, check_redis
from app.routers.audit_log_router      import audit_router
from app.routers.staff_router          import staff_role_router, staff_router
from app.routers.leave_requests_router import leave_router
from app.routers.attendance_router     import attendance_router
from app.routers.company_router        import company_router
from app.routers.system_setting_router import system_setting_router
from app.routers.salaries_router       import salary_router
from app.routers.notification_router   import notification_router
from app.routers.inventory_router      import (
    supplier_router, customer_router, category_router,
    product_router, stock_movement_router, invoice_router,
)
from app.routers.setup_router          import setup_router
from app.routers.ws_router             import ws_router
from app.websockets.ws_manager         import start_redis_pubsub_listener
from app.db.session                    import AsyncSessionLocal
from app.seed.seed                     import seed_data
from app.core.config                   import settings
from app.utils.cloudinary_upload       import init_cloudinary
from app.schemas.schema                import ErrorResponse
from app.core.exceptions               import AppException
from app.routers.chat_router           import chat_router
from app.routers.chat_ws_router        import chat_ws_router
from app.websockets.chat_ws_manager    import start_chat_pubsub_listener
from app.core.rate_limit               import ip_limiter
from app.core.logger                   import logger
from slowapi.errors                    import RateLimitExceeded
from app.middleware import (AuthMiddleware,LoggingMiddleware,ErrorMiddleware,setup_cors)
from slowapi.middleware                 import SlowAPIMiddleware   # ✅ correct import
# /////////////////////////////////
from fastapi.openapi.utils import get_openapi


# =============================================================================
# LIFESPAN — startup + shutdown in one place
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────
    logger.info("Server starting...")
    # Seed data (development only)
    if settings.ENVIRONMENT == "development":
        async with AsyncSessionLocal() as db:
            await seed_data(db)

    # Connect Redis
    await connect_redis()

    # ✅ Check Redis after connecting


    redis_ok = await check_redis()
    if redis_ok:
        logger.info("Redis connected successfully")
    else:
        logger.critical("Redis FAILED — rate limiting will not work!")
    # Cloudinary
    init_cloudinary()

    logger.info("Cloudinary initialized")

    # Start WebSocket pub/sub listeners
    pubsub_task = asyncio.create_task(start_redis_pubsub_listener())
    chat_task   = asyncio.create_task(start_chat_pubsub_listener())
    logger.info("WebSocket listeners started")

    yield

    # ── Shutdown ──────────────────────────────────────────
    logger.info("Server shutting down...")

    # ✅ properly cancel and await tasks
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
    title    = "Backend App",
    version  = "1.0.0",
    lifespan = lifespan,
    # swagger_ui_parameters = {"persistAuthorization": True},  # ✅ keeps token after refresh
)

app.state.limiter = ip_limiter


# =============================================================================
# OPENAPI SECURITY SCHEME  ✅ ADD THIS BLOCK
# =============================================================================

# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     schema = get_openapi(
#         title   = app.title,
#         version = app.version,
#         routes  = app.routes,
#     )
#     schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type":         "http",
#             "scheme":       "bearer",
#             "bearerFormat": "JWT",
#         }
#     }
#     schema["security"] = [{"BearerAuth": []}]
#     app.openapi_schema = schema
#     return schema

# app.openapi = custom_openapi
# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================
# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================



@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    logger.warning(f"SECURITY | Rate limit hit | "f"ip:{request.client.host} | "f"path:{request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "code":    "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please slow down.",
            "action":  "WAIT_AND_RETRY",
        },
        headers={"Retry-After": "60"},
    )



@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code = exc.status_code,
            detail      = exc.detail,
            error_type  = exc.error_type,
        ).dict()
    )


# =============================================================================
# MIDDLEWARE — order matters (last added = first to run)
# =============================================================================


app.add_middleware(ErrorMiddleware)      # outermost — catches everything
app.add_middleware(LoggingMiddleware)    # logs requests + responses
setup_cors(app)                          # CORS
app.add_middleware(AuthMiddleware)       # sets request.state.user_id
app.add_middleware(SlowAPIMiddleware)    # must be last — sees everything ready




# =============================================================================
# ROUTERS
# =============================================================================

app.include_router(setup_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(role_router)
app.include_router(department_router)
app.include_router(router)               # users
app.include_router(audit_router)
app.include_router(staff_role_router)
app.include_router(staff_router)
app.include_router(leave_router)
app.include_router(attendance_router)
app.include_router(system_setting_router)
app.include_router(salary_router)
app.include_router(notification_router)
app.include_router(supplier_router)
app.include_router(customer_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(stock_movement_router)
app.include_router(invoice_router)
app.include_router(chat_router)
app.include_router(ws_router)            # WebSocket
app.include_router(chat_ws_router)       # WebSocket last


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    return {"message": "Backend App is running"}