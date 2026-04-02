from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, extract, func
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from typing import Optional

from app.models.staffs.AttendanceRecord import AttendanceRecord
from app.models.staffs.staff import Staff


class AttendanceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # GET today's record for a staff — used before check-in/out
    # -----------------------------------------------------------------------

    async def get_today_record(
        self, staff_id: int, company_id: int, today: date
    ) -> AttendanceRecord | None:
        result = await self.db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.staff_id   == staff_id,
                AttendanceRecord.company_id == company_id,  # ✅ scope to company
                AttendanceRecord.date       == today,
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # CREATE check-in record
    # -----------------------------------------------------------------------

    async def create_check_in(
        self,
        staff_id:   int,
        company_id: int,   # ✅ required
        today:      date,
        latitude:   str,
        longitude:  str,
    ) -> AttendanceRecord:
        now = datetime.now().time()   # ✅ time object not string

        record = AttendanceRecord(
            company_id     = company_id,   # ✅ required
            staff_id       = staff_id,
            date           = today,
            check_in_time  = now,
            latitude       = latitude,
            longitude      = longitude,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    # -----------------------------------------------------------------------
    # UPDATE check-out on existing record
    # -----------------------------------------------------------------------

    async def update_check_out(
        self,
        record:    AttendanceRecord,
        latitude:  str,
        longitude: str,
    ) -> AttendanceRecord:
        now = datetime.now().time()   # ✅ time object not string — removed debug print

        record.check_out_time = now
        record.latitude       = latitude
        record.longitude      = longitude

        await self.db.commit()
        await self.db.refresh(record)
        return record

    # -----------------------------------------------------------------------
    # GET one by id
    # -----------------------------------------------------------------------

    async def get_by_id(
        self, attendance_id: int, company_id: int
    ) -> AttendanceRecord | None:
        result = await self.db.execute(
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.staff))
            .where(
                AttendanceRecord.attendance_id == attendance_id,
                AttendanceRecord.company_id    == company_id,  # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET all — manager views all staff attendance
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        filter_date: Optional[date] = None,
    ) -> list[AttendanceRecord]:
        query = (
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.staff))
            .where(AttendanceRecord.company_id == company_id)  # ✅ scope to company
            .order_by(
                AttendanceRecord.date.desc(),
                AttendanceRecord.check_in_time,
            )
        )
        if filter_date:
            query = query.where(AttendanceRecord.date == filter_date)

        result = await self.db.execute(query)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET by staff_id — staff views own attendance history
    # -----------------------------------------------------------------------

    async def get_by_staff_id(
        self,
        staff_id:   int,
        company_id: int,
        month:      Optional[int] = None,
        year:       Optional[int] = None,
    ) -> list[AttendanceRecord]:
        # ✅ removed wrong Staff join — just query AttendanceRecord directly
        query = (
            select(AttendanceRecord)
            .where(
                AttendanceRecord.staff_id   == staff_id,
                AttendanceRecord.company_id == company_id,  # ✅ scope to company
            )
            .order_by(AttendanceRecord.date.desc())
        )

        if month and year:
            start = date(year, month, 1)
            end   = (
                date(year + 1, 1, 1)
                if month == 12
                else date(year, month + 1, 1)
            )
            query = query.where(
                AttendanceRecord.date >= start,
                AttendanceRecord.date <  end,
            )
        elif year:
            # ✅ filter by year only if month not provided
            query = query.where(
                extract("year", AttendanceRecord.date) == year
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET by date range
    # -----------------------------------------------------------------------

    async def get_by_date_range(
        self,
        company_id:  int,
        start_date:  date,
        end_date:    date,
        staff_id:    Optional[int] = None,
    ) -> list[AttendanceRecord]:
        query = (
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.staff))
            .where(
                AttendanceRecord.company_id == company_id,
                AttendanceRecord.date       >= start_date,
                AttendanceRecord.date       <= end_date,
            )
            .order_by(AttendanceRecord.date.desc())
        )
        if staff_id:
            query = query.where(AttendanceRecord.staff_id == staff_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # TODAY'S SUMMARY — manager dashboard
    # -----------------------------------------------------------------------

    async def get_today_summary(
        self, company_id: int, today: date
    ) -> dict:
        # ✅ pass company_id
        records     = await self.get_all(company_id, filter_date=today)
        checked_in  = [r for r in records if r.check_in_time]
        checked_out = [r for r in records if r.check_out_time]
        return {
            "date":          str(today),
            "total_present": len(checked_in),
            "checked_out":   len(checked_out),
            "still_in":      len(checked_in) - len(checked_out),
        }

    # -----------------------------------------------------------------------
    # MONTHLY STATS — how many days attended in a month
    # -----------------------------------------------------------------------

    async def get_monthly_stats(
        self,
        staff_id:   int,
        company_id: int,
        month:      int,
        year:       int,
    ) -> dict:
        records = await self.get_by_staff_id(
            staff_id   = staff_id,
            company_id = company_id,
            month      = month,
            year       = year,
        )
        present     = len(records)
        full_days   = [r for r in records if r.check_in_time and r.check_out_time]
        incomplete  = [r for r in records if r.check_in_time and not r.check_out_time]

        return {
            "staff_id":        staff_id,
            "month":           month,
            "year":            year,
            "total_present":   present,
            "full_days":       len(full_days),
            "incomplete_days": len(incomplete),
        }