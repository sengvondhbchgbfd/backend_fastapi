from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_cors(app):
    if settings.ENVIRONMENT == "development":
        # ✅ Allow everything in development
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # ✅ must be False with "*"
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://yourwebapp.com",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
        )