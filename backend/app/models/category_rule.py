import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MatchType(str, enum.Enum):
    CONTAINS = "contains"
    REGEX = "regex"


class CategoryRule(Base):
    """カテゴリ判定用のルール"""

    __tablename__ = "category_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    pattern = Column(String(500), nullable=False)
    match_type = Column(Enum(MatchType), nullable=False, default=MatchType.CONTAINS)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, nullable=False, default=0.5)
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category")

    def __repr__(self) -> str:
        return f"<CategoryRule(id={self.id}, pattern={self.pattern}, category_id={self.category_id})>"
