"""Custom exception types for the AI Employee system.

This module defines a hierarchy of exceptions for better error handling
and recovery throughout the codebase.
"""

from __future__ import annotations


class AIEmployeeError(Exception):
    """Base exception for all AI Employee errors."""

    pass


class VaultError(AIEmployeeError):
    """Error during vault operations (read/write/path validation)."""

    pass


class WatcherError(AIEmployeeError):
    """Error in filesystem or email watcher operations."""

    pass


class APIError(AIEmployeeError):
    """Error calling external APIs (Gmail, etc.).

    Attributes:
        retryable: Whether the error is transient and can be retried
    """

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class SkillError(AIEmployeeError):
    """Error during Agent Skill execution."""

    pass


class ConfigurationError(AIEmployeeError):
    """Error in system configuration or environment setup."""

    pass
