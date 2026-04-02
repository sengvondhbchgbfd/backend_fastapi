import qrcode
import io
import base64
import math
from jose import  jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.core.config import settings

# -------------------------------------------
#  GPS - Haversinse formula
# -------------------------------------------

def calculate_distance_metters(
        late1: float, lon1: float,
        late2: float, lon2: float,
) -> float:
    R        = 6_371_000
    phi1     = math.radians(late1)
    phi2     = math.radians(late2)

    dphi     = math.radians(late2 - late1)

    dlambda = math.radians(lon2 - lon1)
    
    a        = (
        math.sin(dphi / 2 ) ** 2
        + math.cos(phi1) * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def validate_gps_at_office(latitude: str, longitude: str) -> float:
    """"""
    try:
        staff_lat = float(latitude)
        staff_lon = float(longitude)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GPS coordinates. Enable location on your phone.",
        )
    distance = calculate_distance_metters(
        late1=staff_lat,
        lon1=staff_lon,
        late2=settings.OFFICE_LATITUDE,
        lon2=settings.OFFICE_LONGITUDE, 
    )
    
    if distance > settings.OFFICE_RADIUS_METERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message":         "You are not at the office.",
                "distance_meters": round(distance, 1),
                "allowed_radius":  settings.OFFICE_RADIUS_METERS,
                "hint": (
                    f"You are {distance:.0f}m away. "
                    f"Must be within {settings.OFFICE_RADIUS_METERS}m."
                ),
            }
        )
    return distance



# ---------------------------------------------------------------------------
# Office QR token — one token for the whole office
# ---------------------------------------------------------------------------


def create_office_qr_token() -> str:
    payload = {
        "token_type":      "office_qr",
        "office_id": settings.OFFICE_ID,
        "exp":       datetime.utcnow() + timedelta(days=365),
    }
    return jwt.encode(payload, settings.SCAN_SECRET, algorithm=settings.ALGORITHM)
 


# ---------------------------------------------------------------------------
# Office QR token — one token for the whole office
# ---------------------------------------------------------------------------
 
def decode_office_qr_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.SCAN_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("token_type") != "office_qr": #  ///
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid QR. Please scan the office QR on the wall.",
            )
        
        if payload.get("office_id") != settings.OFFICE_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="QR does not belong to this office."
            )
        
        
        return payload["office_id"]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Office QR expired or invalid. Ask manager to reprint.",

        )
    


 
# ---------------------------------------------------------------------------
# QR image generator
# ---------------------------------------------------------------------------


def generate_qr_image_base64(data: str) -> str:
    qr   = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img      = qr.make_image(fill_color="black", back_color="white")
    buffer   = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64      = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"