from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.core.exceptions import (
      NotFoundException,
      ForbiddenException,
      ConflictException
)

# SUPERUSER
SUPERUSER_ROLE_NAME = "superuser"
async def  _get_superuser_role_id(db: AsyncSession) -> int:
      
      pass