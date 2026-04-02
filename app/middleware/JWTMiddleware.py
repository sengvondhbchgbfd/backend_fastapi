from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from jose import jwt, JWTError
from app.core.config import settings


class JWTMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Skip non-protected routes
        if request.url.path in ["/auth/login", "/auth/logout", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Authorization required"}, status_code=401)

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            # Attach user info to request.state
            request.state.user = payload
        except JWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        # Continue to route
        response = await call_next(request)
        return response