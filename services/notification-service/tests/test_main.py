import json
from unittest.mock import MagicMock, patch

from app.consumer import NotificationConsumer


def test_on_message_valid_json():
    consumer = NotificationConsumer()
    consumer.connection = MagicMock()
    consumer.channel = MagicMock()

    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1

    event = {
        "alert_id": "123",
        "product_id": "456",
        "product_name": "Test Product",
        "current_price": 19.99,
        "target_price": 25.00,
        "email": "test@example.com",
        "timestamp": "2024-01-01T00:00:00Z",
    }

    consumer._on_message(channel, method, None, json.dumps(event).encode())
    channel.basic_ack.assert_called_once_with(delivery_tag=1)


def test_on_message_invalid_json():
    consumer = NotificationConsumer()
    consumer.connection = MagicMock()
    consumer.channel = MagicMock()

    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1

    consumer._on_message(channel, method, None, b"not valid json")
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)
