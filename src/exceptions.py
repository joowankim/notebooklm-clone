"""Application exceptions."""


class ApplicationError(Exception):
    """Base application error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(ApplicationError):
    """Resource not found error."""

    pass


class ValidationError(ApplicationError):
    """Validation error."""

    pass


class InvalidStateError(ApplicationError):
    """Invalid state transition error."""

    pass


class ExternalServiceError(ApplicationError):
    """External service error (e.g., API calls)."""

    pass
