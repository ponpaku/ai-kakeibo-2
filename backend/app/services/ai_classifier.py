import json
import subprocess
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.expense import Expense
from app.config import settings


class AIClassifier:
    """AI分類サービス（Claude CLI使用）"""

    @staticmethod
    def classify_expense(
        db: Session,
        expense_data: Dict,
        user_id: int
    ) -> Dict:
        """出費をAIで分類"""
        try:
            # カテゴリ一覧を取得
            categories = db.query(Category).filter(Category.is_active == True).all()
            category_list = [
                {"id": cat.id, "name": cat.name, "description": cat.description}
                for cat in categories
            ]

            # 過去の類似出費を取得（学習のため）
            similar_expenses = AIClassifier._get_similar_expenses(db, expense_data, user_id, limit=5)

            # プロンプトを構築
            prompt = AIClassifier._build_classification_prompt(
                expense_data,
                category_list,
                similar_expenses
            )

            # Claude CLIを実行
            result = AIClassifier._execute_claude_cli(prompt)

            return {
                "success": True,
                "category_id": result.get("category_id"),
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", ""),
                "raw_response": json.dumps(result, ensure_ascii=False)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category_id": None,
                "confidence": 0.0
            }

    @staticmethod
    def _get_similar_expenses(
        db: Session,
        expense_data: Dict,
        user_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """類似する過去の出費を取得"""
        try:
            store_name = expense_data.get("store_name", "")
            description = expense_data.get("description", "")

            # 店名が一致する過去の出費を検索
            query = db.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.category_id.isnot(None)
            )

            if store_name:
                query = query.filter(Expense.store_name.ilike(f"%{store_name}%"))

            similar = query.order_by(Expense.created_at.desc()).limit(limit).all()

            return [
                {
                    "store_name": exp.store_name,
                    "description": exp.description,
                    "amount": float(exp.amount) if exp.amount else None,
                    "category_id": exp.category_id
                }
                for exp in similar
            ]
        except Exception:
            return []

    @staticmethod
    def _build_classification_prompt(
        expense_data: Dict,
        categories: List[Dict],
        similar_expenses: List[Dict]
    ) -> str:
        """分類用のプロンプトを構築"""
        prompt = f"""以下の出費データを分析し、最適なカテゴリを選択してください。

# 出費データ
- 商品名: {expense_data.get('product_name', '不明')}（主要な分類基準）
- 金額: ¥{expense_data.get('amount', 0)}（主要な分類基準）
- 店舗名: {expense_data.get('store_name', '不明')}（補助情報）
- 説明: {expense_data.get('description', '無し')}（補助情報）
- OCRテキスト: {expense_data.get('ocr_raw_text', '無し')[:200]}（補助情報）

# 利用可能なカテゴリ
{json.dumps(categories, ensure_ascii=False, indent=2)}

# 過去の類似出費（参考）
{json.dumps(similar_expenses, ensure_ascii=False, indent=2) if similar_expenses else '無し'}

# 指示
1. 商品名と金額を主要な判断基準として、最も適切なカテゴリを選択してください
2. 店舗名や説明は補助情報として参考にしてください
3. 過去の類似出費がある場合は、一貫性を保つために参考にしてください
4. 信頼度（0.0〜1.0）を算出してください
5. 選択理由を簡潔に説明してください

# 出力形式（JSON）
{{
  "category_id": 選択したカテゴリのID（整数）,
  "confidence": 信頼度（0.0〜1.0の小数）,
  "reasoning": "選択理由"
}}

JSONのみを出力してください。
"""
        return prompt

    @staticmethod
    def _execute_claude_cli(prompt: str) -> Dict:
        """Claude CLIを実行"""
        try:
            # Claude CLIをcode execモードで実行
            cmd = [
                settings.CLAUDE_CLI_PATH,
                "code",
                "exec",
                "--model", settings.CLAUDE_MODEL,
                "--prompt", prompt
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"Claude CLI実行エラー: {result.stderr}")

            # 出力からJSONを抽出
            output = result.stdout.strip()

            # JSON部分を抽出（コードブロックがある場合は除去）
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()
            elif "```" in output:
                json_start = output.find("```") + 3
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()

            # JSONをパース
            result_data = json.loads(output)

            return result_data
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI実行がタイムアウトしました")
        except json.JSONDecodeError as e:
            raise Exception(f"Claude CLIの出力をJSON解析できませんでした: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude CLI実行エラー: {str(e)}")
