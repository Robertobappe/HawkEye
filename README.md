# HawkEye - Price Alert Microservices

A microservices-based price alert system that monitors product prices and notifies users when prices drop below their target. Built as a portfolio project to demonstrate real-world microservices patterns.

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌───────────────────────┐
│   Client    │────────▶│   API Gateway    │────────▶│   Product Service     │
│  (Browser)  │         │    (Nginx)       │         │   (Python/FastAPI)    │
└─────────────┘         └──────────────────┘         │                       │
                               :80                    │  - CRUD Products      │
                                                      │  - Manage Alerts      │
                                                      │  - /health endpoint   │
                                                      │  - Prometheus metrics │
                                                      └───────┬───────────────┘
                                                              │
                                                              │ REST (HTTP)
                                                              ▼
                        ┌──────────────────┐         ┌───────────────────────┐
                        │   RabbitMQ       │◀────────│   Price Watcher       │
                        │   (Broker)       │  Event  │   (Go)                │
                        │                  │         │                       │
                        │  price.alerts.   │         │  - Polls prices       │
                        │  notify (queue)  │         │  - Compares targets   │
                        │                  │         │  - Publishes events   │
                        │  DLX + Dead      │         │  - /health endpoint   │
                        │  Letter Queue    │         └───────────────────────┘
                        └────────┬─────────┘
                                 │
                                 │ AMQP (consume)
                                 ▼
                        ┌───────────────────────┐
                        │  Notification Service  │
                        │  (Python)              │
                        │                        │
                        │  - Consumes events     │
                        │  - Sends email alerts  │
                        │  - Retry + DLQ logic   │
                        │  - /health endpoint    │
                        └────────────────────────┘

        ┌──────────────────────────────────────────────┐
        │              Observability                    │
        │  Prometheus (:9090)  ──▶  Grafana (:3000)    │
        └──────────────────────────────────────────────┘
```

## Tech Stack

| Component              | Technology          | Purpose                              |
|------------------------|---------------------|--------------------------------------|
| Product Service        | Python / FastAPI    | REST API for products & alerts       |
| Price Watcher          | Go                  | Background price comparison worker   |
| Notification Service   | Python              | Event consumer & email notification  |
| Message Broker         | RabbitMQ            | Async communication with DLQ support |
| Database               | PostgreSQL          | Product & alert data persistence     |
| API Gateway            | Nginx               | Reverse proxy & request routing      |
| Monitoring             | Prometheus + Grafana| Metrics collection & dashboards      |
| CI/CD                  | GitHub Actions      | Automated testing & Docker builds    |
| Containerization       | Docker Compose      | Local orchestration of all services  |

## Why These Choices?

- **Two languages (Python + Go)**: Microservices are language-agnostic. Python for rapid API development, Go for the performance-critical background worker.
- **RabbitMQ over Redis Pub/Sub**: RabbitMQ guarantees message delivery with acknowledgments. If the notification service crashes, messages persist in the queue until it recovers. Redis Pub/Sub would lose messages.
- **Dead Letter Queue (DLQ)**: Failed messages are routed to a dead letter queue instead of being lost. This enables debugging and reprocessing of failed notifications.
- **Database-per-service**: The Product Service owns its PostgreSQL database. This enforces loose coupling — services can only communicate through APIs or events, never by sharing a database.
- **Nginx as API Gateway**: A lightweight reverse proxy that routes client requests to the correct service. Simpler than Kong or Traefik for this scale, but demonstrates the pattern.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run Everything

```bash
# Clone the repository
git clone https://github.com/Robertobappe/HawkEye.git
cd HawkEye

# Start all services
docker compose up --build
```

This single command starts:
- PostgreSQL database
- RabbitMQ broker (management UI at http://localhost:15672 — `guest`/`guest`)
- Product Service (http://localhost:8000)
- Price Watcher Service
- Notification Service
- Nginx API Gateway (http://localhost:80)
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000 — `admin`/`admin`)

### Test the API

All requests go through the API Gateway on port `80`:

```bash
# 1. Create a product
curl -X POST http://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro M3",
    "description": "Apple MacBook Pro 14-inch",
    "current_price": 1999.99,
    "url": "https://apple.com/macbook-pro"
  }'

# 2. Create a price alert (use the product ID from step 1)
curl -X POST http://localhost/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "<PRODUCT_ID>",
    "target_price": 2500.00,
    "email": "user@example.com"
  }'

# 3. Check service health
curl http://localhost/health/product-service
curl http://localhost/health/price-watcher
curl http://localhost/health/notification-service

# 4. List all products
curl http://localhost/api/v1/products

# 5. List active alerts
curl http://localhost/api/v1/alerts
```

### Simulate a Price Drop

```bash
# Update the product price to be lower than the alert target
curl -X PUT http://localhost/api/v1/products/<PRODUCT_ID> \
  -H "Content-Type: application/json" \
  -d '{"current_price": 1799.99}'

# Watch the notification-service logs for the simulated email
docker compose logs -f notification-service
```

## Project Structure

```
HawkEye/
├── services/
│   ├── product-service/          # Python/FastAPI — CRUD API
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI application
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   ├── schemas.py        # Pydantic schemas
│   │   │   ├── routes.py         # API endpoints
│   │   │   ├── database.py       # DB connection
│   │   │   └── config.py         # Environment config
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── price-watcher/            # Go — Background worker
│   │   ├── internal/
│   │   │   ├── watcher/          # Price comparison logic
│   │   │   └── rabbitmq/         # RabbitMQ publisher + DLQ
│   │   ├── main.go
│   │   ├── Dockerfile
│   │   └── go.mod
│   │
│   └── notification-service/     # Python — Event consumer
│       ├── app/
│       │   ├── main.py           # Health server + consumer start
│       │   ├── consumer.py       # RabbitMQ consumer with retry
│       │   └── config.py         # Environment config
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── gateway/
│   └── nginx.conf                # API Gateway configuration
│
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml        # Scrape targets
│   └── grafana/
│       └── provisioning/         # Auto-configured datasource
│
├── .github/workflows/
│   └── ci.yml                    # GitHub Actions CI pipeline
│
├── docker-compose.yml            # Full stack orchestration
├── .env.example                  # Environment variables template
└── README.md
```

## Resilience Patterns

### Message Retry & Dead Letter Queue

```
Producer ──▶ Exchange ──▶ Queue (TTL: 60s) ──▶ Consumer
                              │ (on failure)
                              ▼
                    Dead Letter Exchange ──▶ Dead Letter Queue
```

- If the Notification Service **crashes**, messages stay in the queue until it recovers.
- If a message **fails processing**, it is `nack`'d and requeued for retry.
- If a message **cannot be processed** (e.g., invalid JSON), it is sent to the Dead Letter Queue for manual inspection.
- Messages have a **TTL of 60 seconds** — if not consumed in time, they move to the DLQ.

### Health Checks

Every service exposes a `/health` endpoint. Docker Compose uses these to manage startup order and detect failures.

## Monitoring

- **Prometheus** scrapes metrics from the Product Service at `/metrics`
- **Grafana** provides dashboards (auto-configured with Prometheus as datasource)
- **RabbitMQ Management** UI shows queue depth, message rates, and consumer status at http://localhost:15672

## CI/CD Pipeline

GitHub Actions runs on every push and PR:

1. **Python lint** (ruff) for Product Service and Notification Service
2. **Go vet** for Price Watcher
3. **Unit tests** for all services
4. **Docker build** to verify all images compile correctly

## License

MIT
