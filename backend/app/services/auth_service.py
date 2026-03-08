"""Authentication service — register, authenticate, and generate JWT tokens."""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import UserModel, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, authentication, and token generation."""

    def __init__(self, db: Session, secret_key: str, token_expire_minutes: int = 60) -> None:
        self._db = db
        self._repo = UserRepository(db)
        self._secret_key = secret_key
        self._token_expire_minutes = token_expire_minutes

    def register_user(
        self,
        tenant_id: UUID,
        email: str,
        password: str,
        role: str = UserRole.AGENT,
    ) -> UserModel:
        """Register a new user under a tenant.

        Raises ``ValueError`` if a user with the same email already exists
        in the tenant, or if the role is invalid.
        """
        if role not in UserRole.ALL:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {UserRole.ALL}")

        existing = self._repo.get_by_email(tenant_id, email)
        if existing is not None:
            raise ValueError(f"User with email '{email}' already exists in this tenant")

        user = UserModel(
            tenant_id=tenant_id,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
        )
        self._repo.create(user)
        self._db.commit()
        logger.info("Registered user '%s' (role=%s) for tenant %s", email, role, tenant_id)
        return user

    def authenticate_user(self, tenant_id: UUID, email: str, password: str) -> UserModel:
        """Authenticate a user by email and password.

        Raises ``ValueError`` if credentials are invalid or user is inactive.
        """
        user = self._repo.get_by_email(tenant_id, email)
        if user is None:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        return user

    def generate_token(self, user: UserModel) -> str:
        """Generate a JWT access token for an authenticated user."""
        return create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": str(user.tenant_id),
                "role": user.role,
            },
            secret_key=self._secret_key,
            expires_delta=timedelta(minutes=self._token_expire_minutes),
        )
