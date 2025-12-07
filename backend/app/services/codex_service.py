from typing import Dict, List, Optional
import json
import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)


class CodexService:
    """codex exec を使用したOCRと分類サービス"""

    @staticmethod
    def _fallback_category(categories: List[str]) -> Optional[str]:
        if not categories:
            return None

        for candidate in ["その他", "その他 "]:
            if candidate in categories:
                return candidate

        return categories[0]

    @staticmethod
    def get_receipt_schema(categories: List[str]) -> Dict:
        """
        レシートOCR用のJSON Schemaを生成

        Args:
            categories: カテゴリ名のリスト

        Returns:
            Dict: JSON Schema
        """
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["store", "date", "time", "payment", "points", "items"],
            "properties": {
                "store": {"type": ["string", "null"]},
                "date": {"type": ["string", "null"]},
                "time": {"type": ["string", "null"]},
                "payment": {
                    "anyOf": [
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["method", "amount", "card_brand", "card_last4"],
                            "properties": {
                                "method": {"type": ["string", "null"]},
                                "amount": {"type": ["number", "null"]},
                                "card_brand": {"type": ["string", "null"]},
                                "card_last4": {"type": ["string", "null"]}
                            }
                        },
                        {"type": "null"}
                    ]
                },
                "points": {
                    "anyOf": [
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["program", "used", "earned"],
                            "properties": {
                                "program": {"type": ["string", "null"]},
                                "used": {"type": ["number", "null"]},
                                "earned": {"type": ["number", "null"]}
                            }
                        },
                        {"type": "null"}
                    ]
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "quantity", "unit_price", "line_total", "category"],
                        "properties": {
                            "name": {"type": ["string", "null"]},
                            "quantity": {"type": ["number", "null"]},
                            "unit_price": {"type": ["number", "null"]},
                            "line_total": {"type": ["number", "null"]},
                            "category": {
                                "type": "string",
                                "enum": categories
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def get_classification_schema(categories: List[str]) -> Dict:
        """
        分類用のJSON Schemaを生成

        Args:
            categories: カテゴリ名のリスト

        Returns:
            Dict: JSON Schema
        """
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["category", "confidence"],
            "properties": {
                "category": {
                    "type": "string",
                    "enum": categories
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            }
        }

    @staticmethod
    def process_receipt_ocr(
        image_path: str,
        categories: List[str],
        model: str = "gpt-5.1-codex-mini",
        sandbox_mode: str = "read-only",
        skip_git_repo_check: bool = True,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        レシート画像をOCR処理してカテゴリ分類

        Args:
            image_path: レシート画像のパス
            categories: カテゴリ名のリスト
            model: 使用するモデル
            sandbox_mode: サンドボックスモード
            skip_git_repo_check: Gitリポジトリチェックをスキップ

        Returns:
            Dict: {
                "success": bool,
                "data": Dict (成功時),
                "error": str (失敗時),
                "raw_output": str
            }
        """
        schema_file = None
        try:
            # 画像ファイルの存在確認
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

            logger.info(f"Codex OCR処理開始: {image_path}, model={model}")

            # JSON Schemaを一時ファイルに保存
            schema = CodexService.get_receipt_schema(categories)
            schema_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            )
            json.dump(schema, schema_file, ensure_ascii=False, indent=2)
            schema_file.close()

            logger.debug(f"Schema file created: {schema_file.name}")

            # codex execコマンドを構築
            cmd = ["codex", "exec"]

            if skip_git_repo_check:
                cmd.append("--skip-git-repo-check")

            if sandbox_mode:
                cmd.extend(["--sandbox", sandbox_mode])

            categories_json = json.dumps(categories, ensure_ascii=False)
            base_prompt = system_prompt or (
                "あなたは家計簿のレシート読取器です。外部コマンド実行やファイル操作、推測による補完は禁止です。"
                "画像に写っている情報のみを正確に抽出し、カテゴリは必ず候補から1つ選び、迷う場合は『その他』を選択してください。"
                "出力はスキーマに準拠したminified JSONのみ。"
            )
            prompt = (
                f"{base_prompt}\n利用可能なカテゴリ: {categories_json}\n"
                "余計な文章は不要です。スキーマに沿った1つのJSONオブジェクトのみを返してください。"
            )

            cmd.extend([
                "-m", model,
                "-i", image_path,
                "--output-schema", schema_file.name,
                prompt
            ])

            logger.info(f"codex exec command: {' '.join(cmd)}")

            # codex execを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3分タイムアウト
                shell=False,  # セキュリティのため明示的に指定
                check=False   # return codeを手動でチェック
            )

            logger.debug(f"Return code: {result.returncode}")
            logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"codex exec failed (code {result.returncode}): {result.stderr}")

            # 出力をパース
            output = result.stdout.strip()

            if not output:
                raise Exception("codex execの出力が空です")

            # JSONとしてパース
            try:
                data = json.loads(output)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Output: {output}")
                raise Exception(f"JSONパースエラー: {str(e)}")

            fallback_category = CodexService._fallback_category(categories)
            items = data.get("items") if isinstance(data, dict) else None
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue

                    category = item.get("category")
                    if not isinstance(category, str) or category not in categories:
                        logger.warning("OCRアイテムのカテゴリがスキーマに一致しないためフォールバックします")
                        item["category"] = fallback_category

            logger.info(f"OCR成功: store={data.get('store')}, items={len(data.get('items', []))}")

            return {
                "success": True,
                "data": data,
                "raw_output": output
            }

        except subprocess.TimeoutExpired:
            logger.error("codex exec がタイムアウトしました")
            return {
                "success": False,
                "error": "OCR処理がタイムアウトしました",
                "raw_output": None
            }
        except FileNotFoundError as e:
            logger.error(f"ファイルエラー: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_output": None
            }
        except Exception as e:
            logger.exception(f"OCR処理中にエラーが発生: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_output": None
            }
        finally:
            # 一時スキーマファイルを削除
            if schema_file and os.path.exists(schema_file.name):
                try:
                    os.unlink(schema_file.name)
                    logger.debug(f"Schema file deleted: {schema_file.name}")
                except Exception as e:
                    logger.warning(f"Schema file削除失敗: {schema_file.name} - {str(e)}")

    @staticmethod
    def classify_expense(
        product_name: str,
        store_name: Optional[str],
        amount: float,
        note: Optional[str],
        categories: List[str],
        model: str = "gpt-5.1-codex-mini",
        sandbox_mode: str = "read-only",
        skip_git_repo_check: bool = True,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        出費をカテゴリ分類

        Args:
            product_name: 商品名
            store_name: 店舗名
            amount: 金額
            note: 備考
            categories: カテゴリ名のリスト
            model: 使用するモデル
            sandbox_mode: サンドボックスモード
            skip_git_repo_check: Gitリポジトリチェックをスキップ

        Returns:
            Dict: {
                "success": bool,
                "category": str (成功時),
                "confidence": float (成功時),
                "error": str (失敗時)
            }
        """
        schema_file = None
        try:
            logger.info(f"Codex 分類処理開始: product={product_name}, model={model}")

            # JSON Schemaを一時ファイルに保存
            schema = CodexService.get_classification_schema(categories)
            schema_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            )
            json.dump(schema, schema_file, ensure_ascii=False, indent=2)
            schema_file.close()

            input_data = {
                "product_name": product_name,
                "store_name": store_name,
                "amount": amount,
                "note": note
            }
            logger.debug(f"Schema file: {schema_file.name}")

            categories_json = json.dumps(categories, ensure_ascii=False)
            expense_json = json.dumps(input_data, ensure_ascii=False)
            base_prompt = system_prompt or (
                "あなたは家計簿の支出カテゴリ分類器です。外部コマンド実行やファイル操作、推測による補完は禁止です。"
                "次のJSONのみを根拠に分類し、必ず候補から1つ選んでください。迷ったら『その他』を選び、confidenceは0.3以下に設定してください。"
                "出力は余計な文章なしでminified JSONのみ。"
            )

            prompt = (
                f"{base_prompt}\n候補カテゴリ: {categories_json}\n"
                "出力形式: {\"category\":\"<候補>\",\"confidence\":0.0-1.0}\n"
                f"対象JSON: {expense_json}"
            )

            # codex execコマンドを構築
            cmd = ["codex", "exec"]

            if skip_git_repo_check:
                cmd.append("--skip-git-repo-check")

            if sandbox_mode:
                cmd.extend(["--sandbox", sandbox_mode])

            cmd.extend([
                "-m", model,
                "--output-schema", schema_file.name,
                prompt
            ])

            logger.info(f"codex exec command: {' '.join(cmd)}")

            # codex execを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1分タイムアウト
                shell=False,  # セキュリティのため明示的に指定
                check=False   # return codeを手動でチェック
            )

            logger.debug(f"Return code: {result.returncode}")
            logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"codex exec failed (code {result.returncode}): {result.stderr}")

            # 出力をパース
            output = result.stdout.strip()

            if not output:
                raise Exception("codex execの出力が空です")

            # JSONとしてパース
            try:
                data = json.loads(output)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Output: {output}")
                raise Exception(f"JSONパースエラー: {str(e)}")

            fallback_category = CodexService._fallback_category(categories)
            category = data.get("category")
            confidence = data.get("confidence", 0.0)

            if not isinstance(category, str) or category not in categories:
                logger.warning("カテゴリがスキーマに一致しないためフォールバックします")
                category = fallback_category
                confidence = 0.0

            if not isinstance(confidence, (int, float)):
                logger.warning("confidenceが数値ではないため0.0にリセットします")
                confidence = 0.0

            if fallback_category and category == fallback_category and confidence > 0.3:
                confidence = 0.3

            logger.info(f"分類成功: category={category}, confidence={confidence}")

            return {
                "success": True,
                "category": category,
                "confidence": confidence
            }

        except subprocess.TimeoutExpired:
            logger.error("codex exec がタイムアウトしました")
            return {
                "success": False,
                "error": "分類処理がタイムアウトしました"
            }
        except Exception as e:
            logger.exception(f"分類処理中にエラーが発生: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # 一時ファイルを削除
            if schema_file and os.path.exists(schema_file.name):
                try:
                    os.unlink(schema_file.name)
                except Exception as e:
                    logger.warning(f"Schema file削除失敗: {str(e)}")

