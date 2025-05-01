import secrets
import string

from sqlalchemy import inspect

from app.config import settings


async def generate_short_code(length: int = settings.SHORT_CODE_LENGTH) -> str:
    """Generates a random short code."""
    # Using urlsafe characters is generally good practice
    alphabet = string.ascii_letters + string.digits + "-_"
    # Use secrets module for cryptographically secure random generation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

