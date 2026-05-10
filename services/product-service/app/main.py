import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config import settings
from app.database import Base, engine
from app.routes import router
from app.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Product Service started successfully")
    yield


app = FastAPI(
    title="Product Service",
    description="CRUD API for products and price alerts",
    version=settings.service_version,
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
    )


app.include_router(router, prefix="/api/v1", tags=["Products & Alerts"])
