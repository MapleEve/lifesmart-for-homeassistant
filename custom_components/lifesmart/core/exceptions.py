"""Custom exceptions for the LifeSmart integration by @MapleEve"""


class LifeSmartError(Exception):
    """Base exception for all LifeSmart integration errors."""

    pass


class LifeSmartAPIError(LifeSmartError):
    """
    Exception raised for errors returned by the LifeSmart API (non-auth).

    Attributes:
        message -- explanation of the error
        code -- the error code returned by the API
    """

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class LifeSmartAuthError(LifeSmartAPIError):
    """
    Exception raised for authentication failures.

    This is a specific type of API error related to login or token issues.
    """

    pass
