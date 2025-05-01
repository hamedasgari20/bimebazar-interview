from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class URLMapping(Base):
    __tablename__ = "url_mapping"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False, unique=True)
    short_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    visit_count = Column(Integer, default=0, nullable=False)
    # Relationship to VisitLog (optional, useful for ORM features)
    visits = relationship("VisitLog", back_populates="url_mapping", cascade="all, delete-orphan")

    # Individual uniqueness and composite uniqueness
    __table_args__ = (
        UniqueConstraint('short_code', name='uq_url_mapping_short_code'),
        UniqueConstraint('original_url', name='uq_url_mapping_original_url'),
        UniqueConstraint('original_url', 'short_code', name='uq_url_mapping_original_short'),
    )


class VisitLog(Base):
    __tablename__ = "visit_log"

    id = Column(Integer, primary_key=True, index=True)
    url_mapping_id = Column(Integer, ForeignKey("url_mapping.id"), nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    visit_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship back to URLMapping (optional)
    url_mapping = relationship("URLMapping", back_populates="visits")
