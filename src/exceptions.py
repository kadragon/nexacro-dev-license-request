"""
Custom exceptions for Nexacro license requester.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-005
"""


class NexacroError(Exception):
    """Base exception for all Nexacro-related errors."""

    pass


class NetworkError(NexacroError):
    """Network connectivity or timeout errors."""

    pass


class AuthenticationError(NexacroError):
    """Login or credential errors."""

    pass


class LicenseRequestError(NexacroError):
    """License request submission errors."""

    pass
