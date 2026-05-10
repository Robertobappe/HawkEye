import json
import logging
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler

from app.config import settings
from app.consumer import NotificationConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(settings.service_name)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "service": settings.service_name,
                "version": settings.service_version,
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(("0.0.0.0", 8082), HealthHandler)
    logger.info("Health check server starting on :8082")
    server.serve_forever()


def main():
    logger.info("Notification Service starting...")

    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    consumer = NotificationConsumer()
    consumer.start_consuming()


if __name__ == "__main__":
    main()
