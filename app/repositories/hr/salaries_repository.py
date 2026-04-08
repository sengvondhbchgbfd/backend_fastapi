from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date
from decimal import Decimal

from app.models.Salary.salary import Salary
from app.models.Salary import SalaryAdjustment


class SalaryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Salary queries
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        staff_id:    int | None = None,
        status:      str | None = None,
    ) -> list[Salary]:
        query = (
            select(Salary)
            .where(Salary.company_id == company_id)
            .order_by(Salary.created_at.desc())
        )
        if staff_id:
            query = query.where(Salary.staff_id == staff_id)
        if status:
            query = query.where(Salary.payment_status == status)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(
        self, salary_id: int, company_id: int
    ) -> Salary | None:
        result = await self.db.execute(
            select(Salary).where(
                Salary.salary_id  == salary_id,
                Salary.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_my_salaries(
        self, staff_id: int, company_id: int
    ) -> list[Salary]:
        result = await self.db.execute(
            select(Salary)
            .where(
                Salary.staff_id  == staff_id,
                Salary.company_id == company_id,
            )
            .order_by(Salary.pay_period_start.desc())
        )
        return result.scalars().all()

    async def create(self, data: dict) -> Salary:
        salary = Salary(**data)
        self.db.add(salary)
        await self.db.commit()
        await self.db.refresh(salary)
        return salary

    async def update(self, salary: Salary, data: dict) -> Salary:
        for key, value in data.items():
            if value is not None:
                setattr(salary, key, value)
        await self.db.commit()
        await self.db.refresh(salary)
        return salary

    async def delete(self, salary: Salary) -> None:
        await self.db.delete(salary)
        await self.db.commit()

    async def get_summary(self, company_id: int) -> dict:
        total = await self.db.execute(
            select(func.count()).select_from(Salary)
            .where(Salary.company_id == company_id)
        )
        paid = await self.db.execute(
            select(func.count()).select_from(Salary)
            .where(
                Salary.company_id     == company_id,
                Salary.payment_status == "paid",
            )
        )
        pending = await self.db.execute(
            select(func.count()).select_from(Salary)
            .where(
                Salary.company_id     == company_id,
                Salary.payment_status == "pending",
            )
        )
        net_total = await self.db.execute(
            select(func.sum(Salary.net_salary))
            .where(Salary.company_id == company_id)
        )
        return {
            "total_salaries":   total.scalar()    or 0,
            "total_paid":       paid.scalar()     or 0,
            "total_pending":    pending.scalar()  or 0,
            "total_net_amount": net_total.scalar() or Decimal("0"),
        }

    # -----------------------------------------------------------------------
    # Adjustment queries
    # -----------------------------------------------------------------------




    async def get_adjustments(
        self, salary_id: int, company_id: int
    ) -> list[SalaryAdjustment]:
        result = await self.db.execute(
            select(SalaryAdjustment).where(
                SalaryAdjustment.salary_id  == salary_id,
                SalaryAdjustment.company_id == company_id,
            )
        )
        return result.scalars().all()

    async def create_adjustment(self, data: dict) -> SalaryAdjustment:
        adjustment = SalaryAdjustment(**data)
        self.db.add(adjustment)
        await self.db.commit()
        await self.db.refresh(adjustment)
        return adjustment
    


    

    async def delete_adjustment(self, adjustment: SalaryAdjustment) -> None:
        await self.db.delete(adjustment)
        await self.db.commit()

    async def get_adjustment_by_id(
        self, adjustment_id: int, company_id: int
    ) -> SalaryAdjustment | None:
        result = await self.db.execute(
            select(SalaryAdjustment).where(
                SalaryAdjustment.adjustment_id == adjustment_id,
                SalaryAdjustment.company_id    == company_id,
            )
        )
        return result.scalar_one_or_none()