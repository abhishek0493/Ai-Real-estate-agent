"""Generic CRUD base repository."""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Provides generic CRUD operations for any SQLAlchemy model."""

    def __init__(self, model: type[ModelT], db: Session) -> None:
        self._model = model
        self._db = db

    def get_by_id(self, entity_id: int) -> ModelT | None:
        return self._db.get(self._model, entity_id)

    def list(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self._model).offset(skip).limit(limit)
        return list(self._db.scalars(stmt).all())

    def create(self, entity: ModelT) -> ModelT:
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update(self, entity: ModelT) -> ModelT:
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def delete(self, entity_id: int) -> bool:
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True
