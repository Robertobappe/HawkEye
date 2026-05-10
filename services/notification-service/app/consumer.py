import json
import logging
import time

import pika

from app.config import settings

logger = logging.getLogger(settings.service_name)


class NotificationConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        for attempt in range(10):
            try:
                params = pika.URLParameters(settings.rabbitmq_url)
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                logger.info("Connected to RabbitMQ")
                return
            except pika.exceptions.AMQPConnectionError:
                logger.warning(
                    "RabbitMQ connection attempt %d failed. Retrying in 3s...",
                    attempt + 1,
                )
                time.sleep(3)

        raise ConnectionError("Failed to connect to RabbitMQ after 10 attempts")

    def start_consuming(self):
        self.connect()

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=settings.queue_name,
            on_message_callback=self._on_message,
            auto_ack=False,
        )

        logger.info("Waiting for price alert messages on queue: %s", settings.queue_name)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self.channel.stop_consuming()
        finally:
            if self.connection and self.connection.is_open:
                self.connection.close()

    def _on_message(self, channel, method, properties, body):
        try:
            event = json.loads(body)
            logger.info(
                "Price drop alert received! Product: %s | Price: %.2f -> Target: %.2f | Email: %s",
                event.get("product_name", "Unknown"),
                event.get("current_price", 0),
                event.get("target_price", 0),
                event.get("email", "Unknown"),
            )

            self._send_notification(event)

            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message processed and acknowledged (alert_id: %s)", event.get("alert_id"))

        except json.JSONDecodeError:
            logger.error("Invalid JSON message: %s", body)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception:
            logger.exception("Error processing message")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _send_notification(self, event: dict):
        """
        Simulates sending an email notification.
        In production, replace with actual SMTP/SendGrid/SES integration.
        """
        email_body = (
            f"Subject: Price Drop Alert - {event['product_name']}\n"
            f"To: {event['email']}\n"
            f"From: {settings.smtp_from}\n\n"
            f"Great news! The price of '{event['product_name']}' has dropped!\n"
            f"Current Price: ${event['current_price']:.2f}\n"
            f"Your Target Price: ${event['target_price']:.2f}\n"
            f"Timestamp: {event['timestamp']}\n\n"
            f"-- Price Alert Microservices"
        )
        logger.info("[SIMULATED EMAIL]\n%s", email_body)
