"""User management service — tenant-scoped CRUD for dashboard users."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import UserModel, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserManagementService:
    """CRUD operations for tenant users."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = UserRepository(db)

    def list_users(self, tenant_id: UUID) -> list[UserModel]:
        return self._repo.list_by_tenant(tenant_id)

    def create_user(
        self, tenant_id: UUID, email: str, password: str, role: str = UserRole.AGENT,
    ) -> UserModel:
        if role not in UserRole.ALL:
            raise ValueError(f"Invalid role '{role}'")

        existing = self._repo.get_by_email(tenant_id, email)
        if existing is not None:
            raise ValueError(f"User '{email}' already exists in this tenant")

        user = UserModel(
            tenant_id=tenant_id,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True,
        )
        self._repo.create(user)
        self._db.commit()
        logger.info("Created user '%s' (role=%s) for tenant %s", email, role, tenant_id)
        return user

    def delete_user(self, user_id: UUID, tenant_id: UUID) -> None:
        user = self._repo.get_by_id(user_id)
        if user is None or user.tenant_id != tenant_id:
            raise ValueError("User not found")
        self._repo.delete(user)
        self._db.commit()
        logger.info("Deleted user %s from tenant %s", user_id, tenant_id)
