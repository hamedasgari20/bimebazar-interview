import logging
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import url_mapping_repository

logger = logging.getLogger(__name__)


async def increment_visit_count_task(db: AsyncSession, url_mapping_id: int) -> None:
    """Background task to increment visit count."""
    try:
        await url_mapping_repository.increment_visit_count(db, url_mapping_id)
    except Exception as e:
        logger.error(f"Error in increment_visit_count_task: {e}", exc_info=True)


async def create_visit_log_task(
    db: AsyncSession,
    url_mapping_id: int,
    ip_address: str | None,
    user_agent: str | None
) -> None:
    """Background task to create visit log."""
    try:
        await url_mapping_repository.create_visit_log(
            db,
            url_mapping_id=url_mapping_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error in create_visit_log_task: {e}", exc_info=True) 