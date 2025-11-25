"""
Custom exception classes.
"""

from fastapi import HTTPException, status


class InviteTreeException(Exception):
    """Base exception for invite tree system."""
    pass


class InsufficientQuotaException(InviteTreeException):
    """User doesn't have enough invite quota."""
    pass


class InvalidInviteTokenException(InviteTreeException):
    """Invite token is invalid, expired, or already used."""
    pass


class UnauthorizedException(InviteTreeException):
    """User is not authorized for this action."""
    pass


class UserNotFoundException(InviteTreeException):
    """User not found."""
    pass


# HTTP Exception helpers
def unauthorized_error(detail: str = "Not authorized") -> HTTPException:
    """Return 401 Unauthorized error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def forbidden_error(detail: str = "Forbidden") -> HTTPException:
    """Return 403 Forbidden error."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def not_found_error(detail: str = "Not found") -> HTTPException:
    """Return 404 Not Found error."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def bad_request_error(detail: str = "Bad request") -> HTTPException:
    """Return 400 Bad Request error."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )

