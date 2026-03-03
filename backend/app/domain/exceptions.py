"""Domain-level exceptions — pure Python, no framework dependencies."""


class DomainException(Exception):
    """Base exception for all domain-layer errors."""

    def __init__(self, message: str = "Domain error") -> None:
        self.message = message
        super().__init__(message)


class InvalidStateTransition(DomainException):
    """Raised when a lead state transition violates the state machine rules."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Invalid transition: {current} → {target}")


class NegotiationError(DomainException):
    """Raised when the negotiation engine encounters invalid input."""

    def __init__(self, message: str = "Negotiation error") -> None:
        super().__init__(message)


class InvariantViolation(DomainException):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str = "Invariant violation") -> None:
        super().__init__(message)
