import json
import logging
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import RedisManager
from app.repositories import url_mapping_repository
from app.schemas.url_schemas import URLCreate
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
