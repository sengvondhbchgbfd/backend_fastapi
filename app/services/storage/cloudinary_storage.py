import asyncio
import cloudinary
import cloudinary.uploader
import cloudinary.exceptions
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.services.storage.base_storage import BaseStorage

# ── MIME / size constants ─────────────────────────────────────────────────────

ALLOWED_IMAGE_TYPES: set[str] = {
    "image/jpeg", "image/png", "image/webp",
    "image/gif",  "image/svg+xml",
}
ALLOWED_VIDEO_TYPES: set[str] = {
    "video/mp4", "video/mov", "video/avi",
    "video/webm", "video/quicktime",
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


# ── CloudinaryStorage ─────────────────────────────────────────────────────────

class CloudinaryStorage(BaseStorage):
    """
    Concrete implementation of BaseStorage using Cloudinary.
    Call init_cloudinary() once inside lifespan in main.py before using this.
    """

    # ── Internal shared uploader ──────────────────────────
    async def _upload(
        self,
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
                    f"Allowed: {sorted(allowed_types)}"
                ),
            )

        # 2. Read & validate size
        data = await file.read()
        if len(data) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max allowed: {max_size // (1024 * 1024)} MB.",
            )

        # 3. Push to Cloudinary (blocking SDK → thread pool)
        try:
            loop = asyncio.get_event_loop()
            result: dict = await loop.run_in_executor(
                None,
                lambda: cloudinary.uploader.upload(
                    data,
                    resource_type=resource_type,
                    folder=folder,
                    **extra_options,
                ),
            )
        except cloudinary.exceptions.Error as exc:
            raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {exc}")

        return {
            "public_id":     result["public_id"],
            "secure_url":    result["secure_url"],
            "format":        result.get("format"),
            "size":          result.get("bytes"),
            "width":         result.get("width"),       # images only
            "height":        result.get("height"),      # images only
            "duration":      result.get("duration"),    # videos only
            "resource_type": result["resource_type"],
        }

    # ── BaseStorage implementation ────────────────────────

    async def upload_image(self, file: UploadFile, folder: str = "images") -> dict:
        """JPEG / PNG / WebP / GIF / SVG — auto quality + format. Max 10 MB."""
        return await self._upload(
            file=file,
            resource_type="image",
            folder=folder,
            allowed_types=ALLOWED_IMAGE_TYPES,
            max_size=MAX_IMAGE_SIZE,
            extra_options={
                "transformation": [{"quality": "auto", "fetch_format": "auto"}],
            },
        )

    async def upload_video(self, file: UploadFile, folder: str = "videos") -> dict:
        """MP4 / MOV / AVI / WebM — 6 MB chunked upload. Max 200 MB."""
        return await self._upload(
            file=file,
            resource_type="video",
            folder=folder,
            allowed_types=ALLOWED_VIDEO_TYPES,
            max_size=MAX_VIDEO_SIZE,
            extra_options={"chunk_size": 6_000_000},
        )

    async def upload_file(self, file: UploadFile, folder: str = "files") -> dict:
        """PDF / ZIP / CSV / DOCX / XLSX. Max 50 MB."""
        return await self._upload(
            file=file,
            resource_type="raw",
            folder=folder,
            allowed_types=ALLOWED_FILE_TYPES,
            max_size=MAX_FILE_SIZE,
        )

    async def delete_asset(self, public_id: str, resource_type: str = "image") -> dict:
        """Soft-safe delete — returns status dict, never raises on 'not found'."""
        if not public_id or public_id == "string":
            return {"deleted": None, "message": "No valid public_id provided"}

        try:
            loop = asyncio.get_event_loop()
            result: dict = await loop.run_in_executor(
                None,
                lambda: cloudinary.uploader.destroy(
                    public_id, resource_type=resource_type
                ),
            )
        except cloudinary.exceptions.Error as exc:
            raise HTTPException(status_code=500, detail=f"Cloudinary delete failed: {exc}")

        if result.get("result") == "ok":
            return {"deleted": public_id, "status": "deleted"}

        if result.get("result") == "not found":
            return {"deleted": public_id, "status": "already_deleted", "message": "Asset not found (skipped)"}

        raise HTTPException(status_code=500, detail=f"Unexpected Cloudinary response: {result}")


# ── One-time init (call inside lifespan) ──────────────────────────────────────

def init_cloudinary() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )