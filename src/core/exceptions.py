from typing import Any, Dict, Optional


class VeraException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "VERA_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", 500, details)


class DatabaseError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", 503, details)


class CacheError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CACHE_ERROR", 503, details)


class ValidationError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class NotFoundError(VeraException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            f"{resource} not found: {identifier}",
            "NOT_FOUND",
            404,
            {"resource": resource, "identifier": identifier},
        )


class ConflictError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFLICT", 409, details)


class SuppressionError(VeraException):
    def __init__(self, message: str, suppression_key: str):
        super().__init__(
            message,
            "SUPPRESSED",
            429,
            {"suppression_key": suppression_key},
        )


class LLMError(VeraException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LLM_ERROR", 502, details)


class RateLimitError(VeraException):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message,
            "RATE_LIMITED",
            429,
            {"retry_after": retry_after},
        )