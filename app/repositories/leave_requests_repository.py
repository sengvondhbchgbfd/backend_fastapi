from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from datetime import date
from typing import Optional, List

from app.models.staffs.leave_request import LeaveRequest, LeaveStatus, LeaveType
from app.schemas.schema import LeaveRequestCreate, LeaveRequestUpdate


class LeaveRequestRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create(
        self, data: LeaveRequestCreate, staff_id: int, company_id: int
    ) -> LeaveRequest:
        leave = LeaveRequest(
            company_id = company_id,       # ✅ required
            staff_id   = staff_id,
            leave_type = data.leave_type,
            start_date = data.start_date,
            end_date   = data.end_date,
            reason     = data.reason,
            status     = LeaveStatus.pending,  # ✅ always start as pending
        )
        self.db.add(leave)
        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    # =========================================================================
    # GET BY ID
    # =========================================================================

    async def get_by_id(
        self, leave_id: int, company_id: int
    ) -> Optional[LeaveRequest]:
        result = await self.db.execute(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.staff))
            .where(
                LeaveRequest.leave_id   == leave_id,
                LeaveRequest.company_id == company_id,   # ✅ scope to company
            )
        )
        return result.unique().scalar_one_or_none()

    # =========================================================================
    # GET BY STAFF — staff views own requests
    # =========================================================================

    async def get_by_staff_id(
        self,
        staff_id:   int,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> List[LeaveRequest]:
        result = await self.db.execute(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.staff))
            .where(
                LeaveRequest.staff_id   == staff_id,
                LeaveRequest.company_id == company_id,   # ✅ scope to company
            )
            .offset(skip)
            .limit(limit)
            .order_by(LeaveRequest.start_date.desc())
        )
        return result.unique().scalars().all()

    # =========================================================================
    # GET ALL — manager views all
    # =========================================================================

    async def get_all(
        self,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
        status:     Optional[LeaveStatus] = None,  # ✅ was Optional[LeaveType]
        leave_type: Optional[LeaveType]   = None,  # ✅ was Optional[LeaveRequest]
    ) -> List[LeaveRequest]:
        query = (
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.staff))
            .where(LeaveRequest.company_id == company_id)  # ✅ scope to company
        )

        # ✅ apply filters before offset/limit — was applying them wrong
        if status:
            query = query.where(LeaveRequest.status == status)
        if leave_type:
            # ✅ was checking `if LeaveType` (class always truthy) not `if leave_type`
            query = query.where(LeaveRequest.leave_type == leave_type)

        query = (
            query
            .offset(skip)
            .limit(limit)
            .order_by(LeaveRequest.start_date.desc())
        )

        result = await self.db.execute(query)
        return result.unique().scalars().all()

    # =========================================================================
    # GET PENDING — manager approval queue
    # =========================================================================

    async def get_pending(
        self,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> List[LeaveRequest]:
        result = await self.db.execute(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.staff))
            .where(
                LeaveRequest.company_id == company_id,   # ✅ scope to company
                LeaveRequest.status     == LeaveStatus.pending,
            )
            .offset(skip)
            .limit(limit)
            .order_by(LeaveRequest.created_at.desc())
        )
        return result.unique().scalars().all()

    # =========================================================================
    # GET BY DATE RANGE
    # =========================================================================

    async def get_by_date_range(
        self,
        staff_id:   int,
        company_id: int,
        start_date: date,
        end_date:   date,
    ) -> List[LeaveRequest]:
        result = await self.db.execute(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.staff))
            .where(
                LeaveRequest.staff_id   == staff_id,
                LeaveRequest.company_id == company_id,   # ✅ scope to company
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date   >= start_date,
            )
            .order_by(LeaveRequest.start_date)
        )
        return result.unique().scalars().all()

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def update(
        self,
        leave_id:   int,
        company_id: int,
        data:       LeaveRequestUpdate,
    ) -> Optional[LeaveRequest]:
        # ✅ pass company_id
        leave = await self.get_by_id(leave_id, company_id)
        if not leave:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(leave, key, value)

        await self.db.commit()      # ✅ commit not just flush
        await self.db.refresh(leave)
        return leave

    # =========================================================================
    # APPROVE
    # =========================================================================

    async def approve(
        self,
        leave_id:    int,
        company_id:  int,
        approved_by: int,            # staff_id of approver
    ) -> Optional[LeaveRequest]:
        # ✅ was calling update() with wrong signature (passing kwargs not data object)
        leave = await self.get_by_id(leave_id, company_id)
        if not leave:
            return None

        leave.status      = LeaveStatus.approved
        leave.approved_by = approved_by   # ✅ FK → staff.staff_id per schema

        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    # =========================================================================
    # REJECT
    # =========================================================================

    async def reject(
        self,
        leave_id:   int,
        company_id: int,
        reason:     Optional[str] = None,
    ) -> Optional[LeaveRequest]:
        # ✅ was calling update() with wrong signature
        leave = await self.get_by_id(leave_id, company_id)
        if not leave:
            return None

        leave.status = LeaveStatus.rejected
        if reason:
            leave.reason = reason

        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    # =========================================================================
    # CANCEL
    # =========================================================================

    async def cancel(
        self, leave_id: int, company_id: int
    ) -> Optional[LeaveRequest]:
        leave = await self.get_by_id(leave_id, company_id)
        if not leave:
            return None

        leave.status = LeaveStatus.cancelled
        await self.db.commit()
        await self.db.refresh(leave)
        return leave

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete(self, leave_id: int, company_id: int) -> bool:
        leave = await self.get_by_id(leave_id, company_id)
        if not leave:
            return False
        await self.db.delete(leave)
        await self.db.commit()      # ✅ commit not just flush
        return True

    # =========================================================================
    # OVERLAPPING CHECK — prevent duplicate leave requests
    # =========================================================================

    async def get_overlapping(
        self,
        staff_id:         int,
        company_id:       int,
        start_date:       date,
        end_date:         date,
        exclude_leave_id: Optional[int] = None,  # ✅ fixed typo execlude
    ) -> List[LeaveRequest]:
        conditions = [
            LeaveRequest.staff_id   == staff_id,
            LeaveRequest.company_id == company_id,  # ✅ scope to company
            LeaveRequest.status.in_([
                LeaveStatus.pending,
                LeaveStatus.approved,
            ]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date   >= start_date,
        ]
        if exclude_leave_id:
            conditions.append(LeaveRequest.leave_id != exclude_leave_id)

        result = await self.db.execute(
            select(LeaveRequest)
            .where(and_(*conditions))
            .order_by(LeaveRequest.start_date)
        )
        return result.scalars().all()

    # =========================================================================
    # STATS — leave days used
    # =========================================================================

    async def get_days_used(
        self,
        staff_id:   int,
        company_id: int,
        leave_type: LeaveType,
        year:       int,
    ) -> int:
        """Count approved leave days for a staff in a given year."""
        result = await self.db.execute(
            select(
                # ✅ use func.date_part for PostgreSQL not func.julainday (SQLite)
                func.sum(
                    func.date_part(
                        "day",
                        LeaveRequest.end_date - LeaveRequest.start_date
                    ) + 1
                )
            )
            .where(
                LeaveRequest.staff_id   == staff_id,
                LeaveRequest.company_id == company_id,  # ✅ scope to company
                LeaveRequest.leave_type == leave_type,
                LeaveRequest.status     == LeaveStatus.approved,
                extract("year", LeaveRequest.start_date) == year,
            )
        )
        return int(result.scalar() or 0)

    async def get_leave_balance(
        self,
        staff_id:      int,
        company_id:    int,
        leave_type:    LeaveType,
        total_allowed: int,
        year:          int,
    ) -> int:
        used = await self.get_days_used(staff_id, company_id, leave_type, year)
        return max(0, total_allowed - used)

    # =========================================================================
    # COUNTS — summary stats
    # =========================================================================

    async def count_total(self, company_id: int) -> int:
        # ✅ was count_by_total, scope to company
        result = await self.db.execute(
            select(func.count(LeaveRequest.leave_id))
            .where(LeaveRequest.company_id == company_id)
        )
        return result.scalar() or 0

    async def count_by_status(
        self, company_id: int, status: LeaveStatus  # ✅ was LeaveRequest type hint
    ) -> int:
        result = await self.db.execute(
            select(func.count(LeaveRequest.leave_id))
            .where(
                LeaveRequest.company_id == company_id,  # ✅ scope to company
                LeaveRequest.status     == status,
            )
        )
        return result.scalar() or 0