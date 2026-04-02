import cloudinary
import cloudinary.uploader
import cloudinary.exceptions
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import asyncio

 # ─────────────────────────────────────────────────────────────────────────────
# Init  (call once inside lifespan in main.py)
# ─────────────────────────────────────────────────────────────────────────────
def init_cloudinary() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
# ─────────────────────────────────────────────────────────────────────────────
# Allowed MIME types & size limits
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_IMAGE_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}
 
ALLOWED_VIDEO_TYPES: set[str] = {
    "video/mp4",
    "video/mov",
    "video/avi",
    "video/webm",
    "video/quicktime",
}
 
ALLOWED_FILE_TYPES: set[str] = {
    "application/pdf",
    "application/zip",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
 
MAX_IMAGE_SIZE: int = 10  * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE: int = 200 * 1024 * 1024   # 200 MB
MAX_FILE_SIZE:  int = 50  * 1024 * 1024   # 50 MB

# ─────────────────────────────────────────────────────────────────────────────
# Internal shared uploader
# ─────────────────────────────────────────────────────────────────────────────
async def _upload(
    file: UploadFile,
    resource_type: str,
    folder: str,
    allowed_types: set[str],
    max_size: int,
    extra_options: dict | None = None,
) -> dict:
    extra_options = extra_options or {}
 
    # 1. Validate MIME type
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed types: {sorted(allowed_types)}"
            ),
        )
 
    # 2. Read bytes & validate size
    data = await file.read()
    if len(data) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {max_size // (1024 * 1024)} MB.",
        )
 
    # 3. Push to Cloudinary
    try:
        result: dict = cloudinary.uploader.upload(
            data,
            resource_type=resource_type,
            folder=folder,
            **extra_options,
        )
    except cloudinary.exceptions.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary upload failed: {exc}",
        )
 
    return {
        "public_id":     result["public_id"],
        "secure_url":    result["secure_url"],
        "format":        result.get("format"),
        "size":          result.get("bytes"),
        "width":         result.get("width"),        # images only
        "height":        result.get("height"),       # images only
        "duration":      result.get("duration"),     # videos only
        "resource_type": result["resource_type"],
    }
# ─────────────────────────────────────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────────────────────────────────────
async def upload_image(
    file: UploadFile,
    folder: str = "images",
) -> dict:
    """
    Upload an image (JPEG / PNG / WebP / GIF / SVG).
    Auto-optimises quality and format via Cloudinary transformations.
    Max size: 10 MB.
    """
    return await _upload(
        file=file,
        resource_type="image",
        folder=folder,
        allowed_types=ALLOWED_IMAGE_TYPES,
        max_size=MAX_IMAGE_SIZE,
        extra_options={
            "transformation": [{"quality": "auto", "fetch_format": "auto"}],
        },
    )


 
 
async def upload_video(
    file: UploadFile,
    folder: str = "videos",
) -> dict:
    """
    Upload a video (MP4 / MOV / AVI / WebM).
    Uses 6 MB chunks so large files don't time-out.
    Max size: 200 MB.
    """
    return await _upload(
        file=file,
        resource_type="video",
        folder=folder,
        allowed_types=ALLOWED_VIDEO_TYPES,
        max_size=MAX_VIDEO_SIZE,
        extra_options={
            "chunk_size": 6_000_000,  # 6 MB
        },
    )
 
 
async def upload_file(
    file: UploadFile,
    folder: str = "files",
) -> dict:
    """
    Upload a raw file (PDF / ZIP / CSV / DOCX / XLSX).
    Max size: 50 MB.
    """
    return await _upload(
        file=file,
        resource_type="raw",
        folder=folder,
        allowed_types=ALLOWED_FILE_TYPES,
        max_size=MAX_FILE_SIZE,
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

async def delete_asset(
    public_id: str,
    resource_type: str = "image",
) -> dict:

    if not public_id or public_id == "string":
        return {"deleted": None, "message": "No valid public_id provided"}

    try:
        # ✅ Run blocking call in thread pool
        loop = asyncio.get_event_loop()
        result: dict = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
            )
        )
    except cloudinary.exceptions.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary delete failed: {exc}",
        )

    if result.get("result") == "ok":
        return {"deleted": public_id, "status": "deleted"}

    elif result.get("result") == "not found":
        return {
            "deleted": public_id,
            "status": "already_deleted",
            "message": "Asset not found (skip)"
        }

    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Cloudinary response: {result}",
        )
    
# ==================================================================
# Replace assets
# ==================================================================

async def upload_assets(file, folder: str = "companies") -> dict:
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder
        )
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


async def delete_assets(public_id: str):
    if not public_id or public_id == "string":
        return

    try:
        result = cloudinary.uploader.destroy(public_id)

        # safe handling
        if result.get("result") not in ["ok", "not found"]:
            print("⚠️ Unexpected delete result:", result)

    except Exception as e:
        print("⚠️ Delete failed:", e)


        # # -------------------------
        # # 2. Replace Logo  use later
        # # -------------------------

        
        # if logo:
        #     # upload new
        #     uploaded = await upload_asset(logo, folder="companies/logo")

        #     # delete old
        #     if company.logo_public_id:
        #         await delete_asset(company.logo_public_id)

        #     # save new
        #     company.logo_url = uploaded["url"]
        #     company.logo_public_id = uploaded["public_id"]

        # # -------------------------
        # # 3. Replace Banner
        # # -------------------------
        # if banner:
        #     uploaded = await upload_asset(banner, folder="companies/banner")

        #     if company.banner_public_id:
        #         await delete_asset(company.banner_public_id)

        #     company.banner_url = uploaded["url"]
        #     company.banner_public_id = uploaded["public_id"]
