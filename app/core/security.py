from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings
from fastapi import HTTPException, status
import uuid 
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
# ---------------------------------------------------------------------------
# Access token  (60 min)
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    payload        = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    # ✅ FIX 1: use "type" not "token_type"
    payload["token_type"] = "access"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# ----------------------------------------------------------------
# Decode 
# ----------------------------------------------------------------

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        # ✅ FIX 1: check "type" — now matches create_access_token
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code":    "ACCESS_TOKEN_EXPIRED",
                "message": "Access token expired.",
                "action":  "REFRESH_TOKEN",
            },
        )
    
# ---------------------------------------------------------------------------
# Refresh token  (30 days) // change staff_id to user_id
# ---------------------------------------------------------------------------

def create_refresh_token(user_id: int, company_id: int) -> str:
    payload = {
        "user_id": user_id,
        "company_id": company_id,
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),  
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    }

    return jwt.encode(
        payload,
        settings.REFRESH_SECRET,
        algorithm=settings.ALGORITHM
    )

def decode_refresh_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.REFRESH_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code":    "REFRESH_TOKEN_EXPIRED",
                "message": "Session expired. Please login again.",
                "action":  "FULL_LOGIN",
            },
        )


# ---------------------------------------------------------------------------
# Scan token  (15 min)
# ---------------------------------------------------------------------------

def create_scan_token(staff_id: int) -> str:
    payload = {
        "staff_id": staff_id,
        # ✅ FIX 3: "type" not "token_type"
        "token_type":     "scan",
        "exp":      datetime.utcnow() + timedelta(
            minutes=settings.SCAN_TOKEN_EXPIRE_MINUTES
        ),
    }
    return jwt.encode(
        payload, settings.SCAN_SECRET, algorithm=settings.ALGORITHM
    )


def decode_scan_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.SCAN_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        # ✅ FIX 3: check "type" — now matches create_scan_token
        if payload.get("token_type") != "scan":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scan token type.",
            )
        staff_id = payload.get("staff_id")
        if not staff_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Scan token missing staff_id.",
            )
        return int(staff_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code":    "SCAN_TOKEN_EXPIRED",
                "message": "Scan session expired. Please enter your password again.",
                "action":  "RE_AUTHENTICATE",
            },
        )