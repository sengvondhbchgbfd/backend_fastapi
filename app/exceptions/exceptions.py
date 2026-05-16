from fastapi import HTTPException, status



class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_type: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_type = error_type


class NotFoundException(AppException):
    def __init__(self, detail="Resource not found"):
        super().__init__(404, detail, "NOT_FOUND")


class ForbiddenException(AppException):
    def __init__(self, detail="Access forbidden"):
        super().__init__(403, detail, "FORBIDDEN")


class ConflictException(AppException):
    def __init__(self, detail="Conflict with existing resource"):
        super().__init__(409, detail, "CONFLICT")


class UnauthorizedException(AppException):
    def __init__(self, detail="Authentication required"):
        super().__init__(401, detail, "UNAUTHORIZED")


class BadRequestException(AppException):
    def __init__(self, detail="Bad request"):
        super().__init__(400, detail, "BAD_REQUEST")


class UnprocessableException(AppException):
    def __init__(self, detail="Request could not be processed"):
        super().__init__(422, detail, "UNPROCESSABLE")