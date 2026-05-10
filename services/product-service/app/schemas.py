from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    current_price: float = Field(..., gt=0)
    url: str | None = Field(None, max_length=2048)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    current_price: float | None = Field(None, gt=0)
    url: str | None = Field(None, max_length=2048)


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    current_price: float
    url: str | None

    model_config = {"from_attributes": True}


class PriceAlertCreate(BaseModel):
    product_id: UUID
    target_price: float = Field(..., gt=0)
    email: str = Field(..., max_length=255)


class PriceAlertResponse(BaseModel):
    id: UUID
    product_id: UUID
    target_price: float
    email: str
    is_active: str

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
