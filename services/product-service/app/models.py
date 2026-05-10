import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    current_price = Column(Numeric(precision=10, scale=2), nullable=False)
    url = Column(String(2048), nullable=True)


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    target_price = Column(Numeric(precision=10, scale=2), nullable=False)
    email = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
