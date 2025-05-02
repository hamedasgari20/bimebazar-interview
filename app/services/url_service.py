import json
import logging
from typing import Optional, Dict, Any, Tuple

from fastapi import Request, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import RedisManager
from app.repositories import url_mapping_repository
from app.schemas.url_schemas import URLCreate
from app.tasks.url_tasks import increment_visit_count_task, create_visit_log_task
from app.utils.short_code_generator import generate_short_code

logger = logging.getLogger(__name__)


class URLService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = RedisManager()

    def _model_to_dict(self, model) -> Dict[str, Any]:
        """Convert SQLAlchemy model to a serializable dictionary."""
        return {
            'id': model.id,
            'original_url': model.original_url,
            'short_code': model.short_code,
            'created_at': model.created_at.isoformat() if model.created_at else None,
            'visit_count': model.visit_count
        }

    async def get_or_create_short_url(self, url_in: URLCreate) -> Optional[dict]:
        """
        Creates a short URL mapping.
        """
        try:
            original_url = str(url_in.original_url)

            # Try to get from Redis first
            cached_mapping = await self.redis.get(original_url)
            if cached_mapping:
                return json.loads(cached_mapping)

            # Try to get from database
            db_object = await url_mapping_repository.get_url_by_original_url(
                self.db,
                original_url=original_url
            )

            if db_object:
                # Cache the result
                serialized_object = self._model_to_dict(db_object)
                await self.redis.set(original_url, json.dumps(serialized_object))
                return serialized_object

            # Generate new short code and create mapping
            short_code = await generate_short_code()
            new_object = await url_mapping_repository.create_url_mapping(
                db=self.db,
                url_in=url_in,
                short_code=short_code
            )

            # Cache the new mapping
            serialized_object = self._model_to_dict(new_object)
            await self.redis.set(original_url, json.dumps(serialized_object))
            return serialized_object

        except Exception as e:
            logger.error(f"Error in get_or_create_short_url: {e}", exc_info=True)
            raise Exception(f"Failed to create short URL: {str(e)}")

    async def redirect_to_original_url(self, short_code: str, request: Request) -> Tuple[
        Dict[str, Any], BackgroundTasks]:
        """
        Gets the original URL for a short code and returns background tasks for visit logging.
        """
        try:
            # Try to get from Redis first
            cached_mapping = await self.redis.get(f"short_code:{short_code}")
            if cached_mapping:
                url_mapping = json.loads(cached_mapping)
                background_tasks = self._create_visit_background_tasks(url_mapping['id'], request)
                return url_mapping, background_tasks

            # Try to get from database
            db_object = await url_mapping_repository.get_url_by_short_code(
                self.db,
                short_code=short_code
            )

            if not db_object:
                raise ValueError(f"Short URL not found: {short_code}")

            # Cache the result
            serialized_object = self._model_to_dict(db_object)
            await self.redis.set(f"short_code:{short_code}", json.dumps(serialized_object))

            background_tasks = self._create_visit_background_tasks(db_object.id, request)
            return serialized_object, background_tasks

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error in redirect_to_original_url: {e}", exc_info=True)
            raise Exception(f"Failed to get original URL: {str(e)}")

    def _create_visit_background_tasks(self, url_mapping_id: int, request: Request) -> BackgroundTasks:
        """Create background tasks for URL visit."""
        background_tasks = BackgroundTasks()

        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Add tasks to background tasks
        background_tasks.add_task(
            increment_visit_count_task,
            self.db,
            url_mapping_id
        )
        background_tasks.add_task(
            create_visit_log_task,
            self.db,
            url_mapping_id=url_mapping_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return background_tasks

    async def get_url_stats(self, short_code: str):
        """Retrieves statistics for a short code."""
        try:
            # Try to get from Redis first
            cached_stats = await self.redis.get(f"stats:{short_code}")
            if cached_stats:
                return json.loads(cached_stats)

            # If not in Redis, get from database
            db_url = await url_mapping_repository.get_url_by_short_code(self.db, short_code=short_code)
            if not db_url:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

            # Convert to dict and cache in Redis with 1 minute TTL
            serialized_stats = self._model_to_dict(db_url)
            await self.redis.set(f"stats:{short_code}", json.dumps(serialized_stats), ex=60)
            
            return serialized_stats

        except Exception as e:
            logger.error(f"Error in get_url_stats: {e}", exc_info=True)
            raise Exception(f"Failed to get URL stats: {str(e)}")