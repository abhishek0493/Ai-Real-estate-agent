"""Property SQLAlchemy model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PropertyModel(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    bathrooms: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    square_feet: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_properties_tenant_price", "tenant_id", "price"),
    )
