"""User repository — all queries scoped by tenant_id."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserModel


class UserRepository:
    """Concrete repository for dashboard users — every query is tenant-scoped."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, tenant_id: UUID, email: str) -> UserModel | None:
        """Find a user by email within a specific tenant."""
        return self._db.scalars(
            select(UserModel).where(
                UserModel.tenant_id == tenant_id,
                UserModel.email == email,
            )
        ).first()

    def get_by_id(self, user_id: UUID) -> UserModel | None:
        """Find a user by their UUID."""
        return self._db.scalars(
            select(UserModel).where(UserModel.id == user_id)
        ).first()

    def list_by_tenant(self, tenant_id: UUID) -> list[UserModel]:
        """List all users for a tenant."""
        return list(
            self._db.scalars(
                select(UserModel)
                .where(UserModel.tenant_id == tenant_id)
                .order_by(UserModel.created_at.desc())
            ).all()
        )

    def create(self, user: UserModel) -> UserModel:
        """Persist a new user. Flushes but does not commit."""
        self._db.add(user)
        self._db.flush()
        return user

    def delete(self, user: UserModel) -> None:
        """Delete a user."""
        self._db.delete(user)
        self._db.flush()
