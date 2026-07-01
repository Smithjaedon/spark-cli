class InvalidOptionError(Exception):
    """Exception raised for invalid options."""

    pass


class ScaffoldError(Exception):
    """Exception raised for errors during scaffolding."""

    pass


class DependencyError(Exception):
    """Exception raised for errors during dependency installation."""

    pass


class AlembicError(Exception):
    """Exception raised for errors during Alembic setup."""

    pass
