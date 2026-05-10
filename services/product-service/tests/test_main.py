import uuid
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.routes import router
from app.schemas import HealthResponse

test_app = FastAPI()
test_app.include_router(router, prefix="/api/v1")


@test_app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="healthy", service="product-service", version="1.0.0")


mock_db = MagicMock()


def override_get_db():
    yield mock_db


test_app.dependency_overrides[get_db] = override_get_db
client = TestClient(test_app)


def setup_function():
    mock_db.reset_mock()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "product-service"


def test_create_product():
    product_id = uuid.uuid4()

    def refresh_side_effect(obj):
        obj.id = product_id

    mock_db.refresh = MagicMock(side_effect=refresh_side_effect)

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Test Product",
            "description": "A test product",
            "current_price": 29.99,
            "url": "https://example.com/product",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["current_price"] == 29.99
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_list_products():
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert response.json() == []


def test_get_product_not_found():
    mock_db.query.return_value.filter.return_value.first.return_value = None
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/products/{fake_id}")
    assert response.status_code == 404
