from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@product-db:5432/products"
    service_name: str = "product-service"
    service_version: str = "1.0.0"

    model_config = {"env_prefix": "PRODUCT_"}


settings = Settings()
