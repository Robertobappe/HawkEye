from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    queue_name: str = "price.alerts.notify"
    service_name: str = "notification-service"
    service_version: str = "1.0.0"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_from: str = "alerts@pricealert.dev"

    model_config = {"env_prefix": "NOTIFICATION_"}


settings = Settings()
