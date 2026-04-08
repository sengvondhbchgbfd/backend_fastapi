from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from datetime import datetime
from sqlalchemy import select,desc
from sqlalchemy.orm import selectinload
from typing import Optional
class AuditLogRepository:
      def __init__(self, db: AsyncSession):
            self.db = db

            
      async def log(
                  self, 
                  user_id: int,
                  company_id: int,
                  action: str,
                  table_name: str,
                  record_id: int,
                  old_value: dict | None = None,
                  new_value: dict | None = None,
                  ip_address: str | None = None

                  ) -> AuditLog:
                    entry = AuditLog(
                            user_id=user_id,
                            company_id = company_id,
                            action=action,
                            table_name=table_name,
                            record_id=record_id,
                            old_value=old_value,
                            new_value=new_value,
                            ip_address=ip_address,
                        #     created_at=datetime.utcnow()
                    )
                    self.db.add(entry)
                    await self.db.commit()
                    await self.db.refresh(entry)
                    return entry
      
# ──────────────────────────────────────
# Get all logs (newest first)
# ────────────────────────────────────── 
      async def get_all_audit(self, limit: int = 50) -> list[AuditLog]:
              result = await self.db.execute(
                      select(AuditLog)
                      .options(selectinload(AuditLog.user))
                      .order_by(desc(AuditLog.created_at))
                      .limit(limit)                     
              )
              return result.scalars().all()
      

# ──────────────────────────────────────
    # Get logs by user_id
# ──────────────────────────────────────

      async def get_by_user(self, user_id: int, limit: int = 50) -> list[AuditLog]:
                result = await self.db.execute(
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
                )
                return result.scalars().all()
# ──────────────────────────────────────
# Get logs by user_id
# ──────────────────────────────────────
      async def get_by_table(self, table_name: str, limit: int = 50) -> list[AuditLog]:
              result = await self.db.execute(
                      select(AuditLog)
                      .options(selectinload(AuditLog.user))
                      .where(AuditLog.table_name == table_name)
                      .order_by(desc(AuditLog.created_at))
                      .limit(limit)
              )

              return result.scalars().all()
# ──────────────────────────────────────
# Get single log by log_id
# ──────────────────────────────────────
      async def get_by_action(self, action: str, limit: int = 50) -> list[AuditLog]:
              result = await self.db.execute(
                      select(AuditLog)
                      .options(selectinload(AuditLog.user))
                      .where(AuditLog.action == action.upper())
                      .order_by(desc(AuditLog.created_at))
                      .limit(limit)
              )
              return result.scalars().all()

      async def get_by_id(self, log_id: int)-> Optional[AuditLog]:
              result = await self.db.execute(
                      select(AuditLog)
                      .options(selectinload(AuditLog.user))
                      .where(AuditLog.log_id == log_id)
              )
              return result.scalar_one_or_none()
      
      
        

                   
         
            


            