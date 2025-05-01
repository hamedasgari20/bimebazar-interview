import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import url_schemas
from app.services.url_service import URLService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/shorten",
    response_model=url_schemas.URLResponse,
)
async def create_short_url(url_in: url_schemas.URLCreate, session: AsyncSession = Depends(get_db)):
    """
    Create a new short URL mapping.
    """
    service = URLService(session)
    try:
        created_mapping = await service.get_or_create_short_url(url_in=url_in)
        return url_schemas.URLResponse(**created_mapping)
    except ValueError as e:
        logger.error(f"Invalid input: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating short URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating short URL.",
        )


@router.get("/{short_code}")
async def redirect_to_original_url(
        short_code: str,
        request: Request,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_db)):
    service = URLService(session)
    try:
        url_mapping, visit_tasks = await service.redirect_to_original_url(short_code=short_code, request=request)

        # Add the visit tracking tasks to background tasks
        for task in visit_tasks.tasks:
            background_tasks.add_task(task.func, *task.args, **task.kwargs)

        return {"Response": f"{url_mapping['original_url']}"}
    except Exception as e:
        logger.error(f"Error redirecting to URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while redirecting to URL."
        )


@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, session: AsyncSession = Depends(get_db)):
    pass
