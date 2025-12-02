from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base


class AISettings(Base):
    """AI設定（Codex exec用）"""
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, index=True)

    # OCR設定
    ocr_model = Column(String(100), nullable=False, default="gpt-5.1-codex-mini")
    ocr_enabled = Column(Boolean, default=True)

    # 分類設定
    classification_model = Column(String(100), nullable=False, default="gpt-5.1-codex-mini")
    classification_enabled = Column(Boolean, default=True)

    # Codex exec共通設定
    sandbox_mode = Column(String(50), default="read-only")  # read-only, none, etc.
    skip_git_repo_check = Column(Boolean, default=True)

    # プロンプト設定（カスタマイズ可能）
    ocr_system_prompt = Column(Text, nullable=True)
    classification_system_prompt = Column(Text, nullable=True)

    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AISettings(ocr_model={self.ocr_model}, classification_model={self.classification_model})>"
