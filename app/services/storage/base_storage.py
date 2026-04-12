from abc import ABC, abstractmethod
from fastapi import UploadFile
class BaseStorage(ABC):
    """
    Polymorphic storage interface.
    Swap Cloudinary → S3 → local without touching any calling code.

    """
    # ── Upload ────────────────────────────────────────────

    @abstractmethod
    async def upload_image(self, file: UploadFile, folder: str = "images") -> dict: ...

    @abstractmethod
    async def upload_video(self, file: UploadFile, folder: str = "videos") -> dict: ...

    @abstractmethod
    async def upload_file(self, file: UploadFile, folder: str = "files") -> dict: ...


    @abstractmethod
    async def delete_asset(self, public_id: str, resource_type: str = "image") -> dict: ...

    # ── Delete ────────────────────────────────────────────
    
    # ── Quick replace helpers (upload + delete old) ───────
    
    async def replace_asset(
        self,
        file: UploadFile,
        old_public_id: str | None,
        folder: str,
        kind: str = "image",          # "image" | "video" | "file"
    ) -> dict:
        """
        Upload new asset, then delete the old one.
        Returns the new asset dict.
        """
        if kind == "video":
            result = await self.upload_video(file, folder)
        elif kind == "file":
            result = await self.upload_file(file, folder)
        else:
            result = await self.upload_image(file, folder)

        if old_public_id:
            await self.delete_asset(old_public_id, resource_type=kind if kind != "file" else "raw")

        return result