"""Custom exceptions for business logic errors."""


class VinylPlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class CampaignNotActiveError(VinylPlatformError):
    """Raised when an operation requires an active campaign."""


class InsufficientCapacityError(VinylPlatformError):
    """Raised when campaign has no remaining capacity for pre-orders."""


class InvalidStateTransitionError(VinylPlatformError):
    """Raised when a state machine transition is not allowed."""


class ArtworkDeadlinePassedError(VinylPlatformError):
    """Raised when artwork upload deadline has passed."""
