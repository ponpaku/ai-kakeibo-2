import re
import unicodedata
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category_rule import CategoryRule, MatchType


class CategoryRuleService:
    """カテゴリルールの適用と補助処理"""

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKC", text).strip().lower()
        return CategoryRuleService._katakana_to_hiragana(normalized)

    @staticmethod
    def _katakana_to_hiragana(text: str) -> str:
        chars = []
        for ch in text:
            code = ord(ch)
            if 0x30A1 <= code <= 0x30F6:
                chars.append(chr(code - 0x60))
            else:
                chars.append(ch)
        return "".join(chars)

    @staticmethod
    def validate_regex(pattern: str) -> None:
        try:
            re.compile(pattern)
        except re.error as exc:  # pragma: no cover - defensive
            raise ValueError(f"無効な正規表現です: {exc}")

    @staticmethod
    def find_match(db: Session, text_candidates: List[str]) -> Optional[CategoryRule]:
        normalized_texts = [CategoryRuleService.normalize_text(t) for t in text_candidates if t]
        if not normalized_texts:
            return None
        target = " ".join(t for t in normalized_texts if t)
        if not target:
            return None

        rules = db.query(CategoryRule).filter(CategoryRule.is_active == True).order_by(
            CategoryRule.priority.asc(), CategoryRule.id.asc()
        ).all()

        for rule in rules:
            if rule.match_type == MatchType.CONTAINS:
                tokens = [CategoryRuleService.normalize_text(token) for token in rule.pattern.split("|")]
                if any(token and token in target for token in tokens):
                    return rule
            else:
                try:
                    if re.search(rule.pattern, target):
                        return rule
                except re.error:
                    continue
        return None

    @staticmethod
    def test_rule(db: Session, text: str) -> Optional[CategoryRule]:
        return CategoryRuleService.find_match(db, [text])
