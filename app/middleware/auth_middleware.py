from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token

# Routes that do NOT need access token
PUBLIC_ROUTES = [
    "/auth/login",
    "/auth/refresh",
    "/auth/logout",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
]


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # ── 1. Skip public routes ──────────────────────────
        if any(request.url.path.startswith(route) for route in PUBLIC_ROUTES):
            return await call_next(request)

        # ── 2. Check Authorization header exists ───────────
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code":    "MISSING_TOKEN",
                    "message": "Authorization header missing.",
                    "action":  "FULL_LOGIN",
                }
            )

        # ── 3. Decode and validate access token ────────────
        token = auth_header.split(" ")[1]

        try:
            payload = decode_access_token(token)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code":    "INVALID_TOKEN",
                    "message": "Token is invalid.",
                    "action":  "FULL_LOGIN",
                }
            )

        # ── 4. Attach user info to request state ───────────
        request.state.user_id    = payload.get("sub")
        request.state.company_id = payload.get("company_id")

        return await call_next(request)