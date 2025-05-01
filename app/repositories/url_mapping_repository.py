from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import URLMapping, VisitLog
from app.schemas.url_schemas import URLCreate


async def get_url_by_short_code(db: AsyncSession, short_code: str) -> URLMapping | None:
    """Fetches a URLMapping by its short code."""
    stmt = select(URLMapping).where(URLMapping.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_url_by_original_url(db: AsyncSession, original_url: str) -> URLMapping | None:
    """Fetches a URLMapping by its original URL (useful to avoid duplicates)."""
    stmt = select(URLMapping).where(URLMapping.original_url == original_url)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_url_mapping(db: AsyncSession, *, url_in: URLCreate, short_code: str) -> URLMapping:
    """Creates a new URLMapping entry."""
    db_obj = URLMapping(
        original_url=str(url_in.original_url),
        short_code=short_code
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def increment_visit_count(db: AsyncSession, url_mapping_id: int) -> None:
    """Increments the visit count for a URL mapping."""
    stmt = update(URLMapping).where(URLMapping.id == url_mapping_id).values(
        visit_count=URLMapping.visit_count + 1
    )
    await db.execute(stmt)
    await db.commit()


async def create_visit_log(db: AsyncSession, url_mapping_id: int, ip_address: str | None, user_agent: str | None) -> None:
    """Creates a new visit log entry."""
    visit_log = VisitLog(
        url_mapping_id=url_mapping_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(visit_log)
    await db.commit()
