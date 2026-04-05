from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# Root path (one level up from alembic/)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# //////////////////////////////////////////////////

from app.db.base import Base
from app.models.users import User
from app.models.roles import Role
from app.models.staffs import LeaveRequest, Staff, StaffRole, leave_request, AttendanceRecord
from app.models.departments import Department
from app.models.chat import ChatGroup, ChatMessage, ChatGroupMember
from app.models.invoices import Invoice, InvoiceItem
from app.models.products import Product, StockMovement, ProductImage
from app.models.Salary import Salary, SalaryAdjustment
from app.models.audit_log import AuditLog
from app.models import Category
from app.models.notification import Notification
from app.models.supplier import Supplier
from app.models.system_setting import SystemSetting
from app.models.company import Company
from app.models.refresh_token import RefreshToken
from app.models.CompanyStatusHistory import CompanyStatusHistory



from app.core.config import settings

# /////////////////////  connect to postgreesql  ////////////////////////////

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# /////////////////////////////////////////////////


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()