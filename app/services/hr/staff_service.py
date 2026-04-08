from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
import redis.asyncio as redis
from fastapi import  Depends, status,UploadFile
from app.models.staffs.staff import Staff
from app.models.staffs.staff_role import StaffRole
from app.schemas.schema import StaffRoleCreate, StaffRoleUpdate, StaffCreate, StaffUpdate
from app.repositories.hr.staff_repository import StaffRepository, StaffRolesRepository
from app.repositories.auth.user_respo import UserRepository
from app.services.communication.notifications_service import NotificationService
from app.dependencies import get_db, get_redis_client
from typing import Optional


# //////////////////////////////////////////////////////////

from app.services.storage import CloudinaryStorage
storage = CloudinaryStorage()

# ===========================================================================
# STAFF ROLE SERVICE — no notifications needed
# ===========================================================================

class StaffRoleService:

    def __init__(self, repo: StaffRolesRepository):
        self.repo = repo




    async def create(self, data: StaffRoleCreate, company_id: int) -> StaffRole:
        existing = await self.repo.get_by_name(data.role_name, company_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Staff role '{data.role_name}' already exists.",
            )
        return await self.repo.create(data, company_id)





    async def get_by_id(self, staff_role_id: int, company_id: int) -> StaffRole:
        staff_role = await self.repo.get_by_id(staff_role_id, company_id)
        if not staff_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Staff role id={staff_role_id} not found.",
            )
        return staff_role
    



    async def get_all(self, company_id: int) -> list[StaffRole]:
        return await self.repo.get_all(company_id)

    async def update(
        self,
        staff_role_id: int,
        data:          StaffRoleUpdate,
        company_id:    int,
    ) -> StaffRole:
        


        await self.get_by_id(staff_role_id, company_id)
        return await self.repo.update(
            staff_role_id,
            data.model_dump(exclude_none=True),
            company_id,
        )

    async def delete(self, staff_role_id: int, company_id: int) -> None:
        deleted = await self.repo.delete(staff_role_id, company_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Staff role id={staff_role_id} not found.",
            )


async def get_staff_role_service(
    db: AsyncSession = Depends(get_db),
) -> StaffRoleService:
    return StaffRoleService(StaffRolesRepository(db))


# ===========================================================================
# STAFF SERVICE — with notifications
# ===========================================================================

class StaffService:

    def __init__(
        self,
        db:           AsyncSession,        # ✅ needed for NotificationService
        repo:         StaffRepository,
        user_repo:    UserRepository,
        redis_client: redis.Redis,         # ✅ for real-time push
    ):
        self.repo      = repo
        self.user_repo = user_repo
        self.notif     = NotificationService(  # ✅
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # GET all
    # -----------------------------------------------------------------------

    async def get_all(self, company_id: int) -> list[Staff]:
        return await self.repo.get_all(company_id)

    # -----------------------------------------------------------------------
    # GET by id
    # -----------------------------------------------------------------------

    async def get_by_id(self, staff_id: int, company_id: int) -> Staff:
            staff = await self.repo.get_by_id(staff_id, company_id)
            if not staff:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Staff id={staff_id} not found.",
                )
            return staff
    
    
    
    # -----------------------------------------------------------------------
    # GET by user_id
    # -----------------------------------------------------------------------

    async def get_by_user_id(self, user_id: int, company_id: int) -> Staff:
        staff = await self.repo.get_by_user_id(user_id, company_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Staff with user_id={user_id} not found.",
            )
        return staff

    # -----------------------------------------------------------------------
    # GET by role
    # -----------------------------------------------------------------------

    async def get_by_role(
        self, staff_role_id: int, company_id: int
    ) -> list[Staff]:
        return await self.repo.get_by_role(staff_role_id, company_id)

    # -----------------------------------------------------------------------
    # GET managers
    # -----------------------------------------------------------------------

    async def get_managers(self, company_id: int) -> list[Staff]:
        return await self.repo.get_managers(company_id)

    # -----------------------------------------------------------------------
    # GET by department
    # -----------------------------------------------------------------------

    async def get_by_department(
        self, department_id: int, company_id: int
    ) -> list[Staff]:
        return await self.repo.get_by_department(department_id, company_id)

    # -----------------------------------------------------------------------
    # CREATE staff — notify linked user
    # -----------------------------------------------------------------------

    async def create(
        self,
        data:        StaffCreate,
        company_id:  int,
        avatar_file: Optional[UploadFile] = None,
    ) -> Staff:
 
        # 1. Verify linked user exists in same company
        if data.user_id:
            user = await self.user_repo.get_by_id(data.user_id, company_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User id={data.user_id} not found.",
                )
 
            # 2. Check no duplicate staff for this user
            already_exists = await self.repo.exists_by_user_id(data.user_id, company_id)
            if already_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Staff record already exists for user_id={data.user_id}.",
                )
 
        # 3. Check email unique within company
        if data.email:
            email_conflict = await self.repo.get_by_email(data.email, company_id)
            if email_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{data.email}' is already in use.",
                )
 
        # 4. Handle avatar upload — Cloudinary
        staff_data = data.model_dump(exclude_none=True)
        staff_data["company_id"] = company_id
 
        if avatar_file and avatar_file.filename:
            folder        = f"staff/company_{company_id}"
            upload_result = await storage.upload_image(avatar_file, folder=folder)
            staff_data["avatar_url"]       = upload_result["secure_url"]
            staff_data["avatar_public_id"] = upload_result["public_id"]
 
        # 5. Create staff
        staff = Staff(**staff_data)
        staff = await self.repo.create(staff)
 
        # 6. ✅ notify linked user — staff profile created
        if data.user_id:
            await self.notif.send(
                company_id     = company_id,
                user_id        = data.user_id,
                title          = "Staff profile created",
                message        = (
                    "Your staff profile has been set up. "
                    "You can now scan attendance and submit leave requests."
                ),
                notif_type     = "success",
                reference_id   = staff.staff_id,
                reference_type = "staff",
            )
 
        return staff
    




    # ===========================================================
    #  update 
    # ===========================================================


    async def update(
    self,
    staff_id: int,
    data: StaffUpdate,
    company_id: int,
    avatar_file: Optional[UploadFile] = None
    ) -> Staff:

        existing = await self.repo.get_by_id(staff_id, company_id)
        update_data = data.model_dump(exclude_unset=True)
        if avatar_file and avatar_file.filename:
            folder = f"staff/company_{company_id}"
            upload_result = await storage.upload_image(avatar_file, folder=folder)

            update_data["avatar_url"] = upload_result["secure_url"]
            update_data["avatar_public_id"] = upload_result["public_id"]
            

            if existing.avatar_public_id:
                try:
                    result = await storage.delete_asset(existing.avatar_public_id, resource_type="image")
                except Exception as e:
                    print(f"[DEBUG] Delete failed {e}")
        if update_data.get("email"):
            email_conflict = await self.repo.get_by_email(update_data["email"], company_id)
            if email_conflict and email_conflict.staff_id != staff_id:
                raise HTTPException(status_code=409, detail="Email already in use.")
        updated = await self.repo.update(staff_id, update_data, company_id)
        if update_data:
            await self.notif.send(
                company_id     = company_id,
                user_id        = existing.user_id,
                title          = "Staff profile updated",
                message        = "Your staff profile has been updated.",
                notif_type     = "success",
                reference_id   = staff_id,
                reference_type = "staff",
            )

        return updated
    


    # ===========================================================
    #  only avartar
    # ===========================================================

    
    async def update_staff_avatar(
            self,
            staff_id:         int,
            company_id:       int,
            avatar_file:      UploadFile,       
            avatar_public_id: str | None,    
        ) -> Staff:

            staff = await self.repo.get_by_id(staff_id, company_id)
            if not staff:
                raise HTTPException(status_code=404, detail="Staff not found.")
            old_public_id = staff.avatar_public_id or avatar_public_id
            if old_public_id:
                await storage.delete_asset(old_public_id)
            upload_result = await storage.upload_image(
                file   = avatar_file,
                folder = f"staff/company_{company_id}",   
            )

            updated = await self.repo.update_avatar(
                staff_id         = staff_id,
                company_id       = company_id,
                avatar_url       = upload_result["secure_url"],   
                avatar_public_id = upload_result["public_id"],  
            )

            return updated



    # -----------------------------------------------------------------------
    # DELETE staff
    # -----------------------------------------------------------------------

    async def delete(self, staff_id: int, company_id: int) -> dict:
        staff   = await self.get_by_id(staff_id, company_id)
        deleted = await self.repo.delete(staff_id, company_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete staff.",
            )
        return {"message": f"Staff '{staff.name}' deleted successfully."}


# ===========================================================================
# FACTORY
# ===========================================================================

async def get_staff_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),  # ✅ inject redis
) -> StaffService:
    return StaffService(
        db           = db,
        repo         = StaffRepository(db),
        user_repo    = UserRepository(db),
        redis_client = redis_client,
    )