import logging

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.config.settings import get_settings
from app.observability.logging.config import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。"""
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)
    app.include_router(health_router)
    logger.info(
        "application_configured",
        extra={"fields": {"app_name": settings.app_name, "app_env": settings.app_env}},
    )
    return app


app = create_app()
