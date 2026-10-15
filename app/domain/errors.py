class DomainError(Exception):
    """Base class for business errors. Handlers map each subclass to an HTTP status."""


class EmailAlreadyExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class InvalidTokenError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class InvalidFilterError(DomainError):
    pass
