from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            # Web
            "http://localhost:3000",
            "http://localhost:5173",
            "https://yourwebapp.com",

            # Mobile (Flutter dev)
            "http://localhost:8080",
            "http://10.0.2.2:8000",   # Android emulator → host machine
        ],
        allow_credentials=True,       # required for HttpOnly cookies (web)
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )