from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from jose import jwt, JWTError
from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException, AppException
import logging
from typing import Dict, Optional, List, Callable


logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()

# ---------------------------------------------------------------------------
# get superuser currently
# ---------------------------------------------------------------------------


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), ) -> Dict:
    """"""
    return decode_access_token(credentials.credentials)





    
def require_login(
        current_user:  dict = Depends(get_current_user)
)  ->  dict:
    """"""
    if not  current_user:
        raise UnauthorizedException("Authentication required.")
    return current_user




def require_staff(current_user: dict = Depends(require_login)) -> dict:
    if not current_user.get("staff_id"):
        raise UnauthorizedException("Authentication required.")
    return current_user



# ---------------------------------------------------------------------------
# get superuser 
# ---------------------------------------------------------------------------

def require_superuser(current_user: dict = Depends(get_current_user)) -> Dict:
    if current_user.get("role") != "superuser":
        raise ForbiddenException("Superuser access required.")
    return current_user




def require_admin(current_user: Dict = Depends(get_current_user), ) -> Dict:
    """"""
    role = current_user.get("role")
    if role not in ["admin", "superuser"]:
        logger.warning(
            f'Admin access deinied for user {current_user.get("sub")}'
        )
        raise ForbiddenException("Admin access required  or superuser only.")
    return current_user





# -----------------------------------------------------------------------
# 
# -----------------------------------------------------------------------





def require_manager(current_user: dict = Depends(require_login), ) -> dict:
    """"""
    role = current_user.get("role")
    if role not in ["manager", "admin", "superuser"]:
        logger.warning(
            f'Manager access decied for user {current_user.get("sub")}'
        )
        raise ForbiddenException("Manager access required.")
    return current_user





def require_employee(
        current_user: Dict = Depends(get_current_user),

) -> Dict:
    """"""
    if not current_user:
        raise UnauthorizedException("Authentiaction required.")
    return current_user




def require_permission(permission: str):
    def _check(current_user: dict = Depends(get_current_user)) -> dict:
        perms = current_user.get("permissions", [])

        if "*" in perms or permission in perms:
            return current_user
        raise ForbiddenException(f"Permission required: {permission}")

    return _check

def require_any_permission(permission: List[str]) -> Callable:
    """"""


