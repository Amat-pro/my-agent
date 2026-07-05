"""系统健康检查路由。"""

import logging

from fastapi import APIRouter

from app.api.schemas.health import HealthResponse

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """返回服务健康状态。"""
    logger.info(
        "health_check_requested",
        extra={"fields": {"status": "ok", "test_count": 1, "test_num": 3}},
    )
    return HealthResponse(status="ok")
