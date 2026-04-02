from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DEBUG: bool = True
    # -------------------------------------------------------------------------
    # Environment
    # -------------------------------------------------------------------------
    ENVIRONMENT: str = "production"   # ✅ add this — controls seed

    # -------------------------------------------------------------------------
    # Admin (for seed data only)
    # -------------------------------------------------------------------------
    ADMIN_USERNAME: str = "admin"     # ✅ default so setup doesn't need it
    ADMIN_PASSWORD: str = "admin123"

    # -------------------------------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------------------------------
    POSTGRES_USER:     str
    POSTGRES_PASSWORD: str
    POSTGRES_DB:       str
    POSTGRES_HOST:     str
    POSTGRES_PORT:     int
    DATABASE_URL:      str

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    REDIS_HOST:     str = "redis"
    REDIS_PORT:     int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB:       int = 0

    # -------------------------------------------------------------------------
    # JWT tokens
    # -------------------------------------------------------------------------
    SECRET_KEY:                  str
    ALGORITHM:                   str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8   # 8 hours

    REFRESH_SECRET:            str
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30          # 30 days

    # -------------------------------------------------------------------------
    # Scan token (attendance QR)
    # -------------------------------------------------------------------------
    SCAN_SECRET:               str
    SCAN_TOKEN_EXPIRE_MINUTES: int = 15          # 15 minutes

    # ------------------------------------------------------------------------
    # set image to cloud
    # ------------------------------------------------------------------------
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY:    str
    CLOUDINARY_API_SECRET: str
    # -------------------------------------------------------------------------
    # Office GPS
    # -------------------------------------------------------------------------
    OFFICE_ID:             str
    OFFICE_LATITUDE:       float = 11.5564
    OFFICE_LONGITUDE:      float = 104.9282
    OFFICE_RADIUS_METERS:  int   = 100   # ✅ fixed typo READIUS_METTERS


    OFFICE_OPEN_TIME:  str = "09:00"   # office opens
    OFFICE_CLOSE_TIME: str = "17:00" 

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = {
        "env_file": ".env",
        "extra":    "ignore",
    }


settings = Settings()