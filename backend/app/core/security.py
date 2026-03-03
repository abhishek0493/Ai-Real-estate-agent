"""Security utilities — API key generation."""

import secrets


def generate_api_key() -> str:
    """Generate a cryptographically secure, URL-safe API key.

    Uses 32 bytes of entropy (256 bits), resulting in a ~43 character
    URL-safe string.
    """
    return secrets.token_urlsafe(32)
