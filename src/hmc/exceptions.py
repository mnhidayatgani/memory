"""Exception hierarchy for HMC package.

This module defines custom exceptions for different error scenarios in the
Hybrid Memory Core system.
"""


class HMCError(Exception):
    """Base exception for all HMC errors.

    All custom exceptions in the HMC package inherit from this base class,
    allowing users to catch all HMC-related errors with a single except clause.
    """

    pass


class StorageError(HMCError):
    """Exception raised for storage backend errors.

    This includes database connection failures, read/write errors,
    and other storage-related issues in both factual and semantic backends.

    Args:
        message: Human-readable error description
        original_error: Optional underlying exception that caused this error
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class ValidationError(HMCError):
    """Exception raised for input validation failures.

    Raised when user input does not meet the expected format or constraints,
    such as invalid project IDs, empty keys, or malformed metadata.

    Args:
        message: Human-readable description of the validation failure
        field: Optional name of the field that failed validation
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class SeederError(HMCError):
    """Exception raised for seeding operation failures.

    Raised during project seeding when files cannot be read, parsed,
    or processed correctly.

    Args:
        message: Human-readable error description
        file_path: Optional path to the file that caused the error
    """

    def __init__(self, message: str, file_path: str | None = None) -> None:
        super().__init__(message)
        self.file_path = file_path
