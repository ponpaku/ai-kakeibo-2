from typing import Dict, List, Optional
import json
import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)


class CodexService:
    """Codex exec を使用したOCRと分類サービス"""

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
                                "type": ["string", "null"],
                                "enum": categories + [None]
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
                    "type": ["string", "null"],
                    "enum": categories + [None]
                },
                "confidence": {
                    "type": ["number", "null"],
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
        skip_git_repo_check: bool = True
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

            # Codex execコマンドを構築
            cmd = ["codex", "exec"]

            if skip_git_repo_check:
                cmd.append("--skip-git-repo-check")

            if sandbox_mode:
                cmd.extend(["--sandbox", sandbox_mode])

            cmd.extend([
                "-m", model,
                "-i", image_path,
                "--output-schema", schema_file.name,
                "Return ONLY one minified JSON object that conforms to the schema. "
                "No extra text. No spaces/newlines outside strings. "
                "Use null if unsure. Do not invent items. "
                "Extract all visible information from the receipt image accurately."
            ])

            logger.info(f"Codex exec command: {' '.join(cmd)}")

            # Codex execを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3分タイムアウト
            )

            logger.debug(f"Return code: {result.returncode}")
            logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"Codex exec failed (code {result.returncode}): {result.stderr}")

            # 出力をパース
            output = result.stdout.strip()

            if not output:
                raise Exception("Codex execの出力が空です")

            # JSONとしてパース
            try:
                data = json.loads(output)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Output: {output}")
                raise Exception(f"JSONパースエラー: {str(e)}")

            logger.info(f"OCR成功: store={data.get('store')}, items={len(data.get('items', []))}")

            return {
                "success": True,
                "data": data,
                "raw_output": output
            }

        except subprocess.TimeoutExpired:
            logger.error("Codex exec がタイムアウトしました")
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
        skip_git_repo_check: bool = True
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
        input_file = None
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

            # 入力データを一時ファイルに保存
            input_data = {
                "product_name": product_name,
                "store_name": store_name,
                "amount": amount,
                "note": note
            }
            input_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            )
            json.dump(input_data, input_file, ensure_ascii=False, indent=2)
            input_file.close()

            logger.debug(f"Input file: {input_file.name}")
            logger.debug(f"Schema file: {schema_file.name}")

            # Codex execコマンドを構築
            cmd = ["codex", "exec"]

            if skip_git_repo_check:
                cmd.append("--skip-git-repo-check")

            if sandbox_mode:
                cmd.extend(["--sandbox", sandbox_mode])

            cmd.extend([
                "-m", model,
                "-i", input_file.name,
                "--output-schema", schema_file.name,
                f"Based on the expense data (product_name, store_name, amount, note), "
                f"classify it into one of the following categories: {', '.join(categories)}. "
                f"Return ONLY one minified JSON object with 'category' and 'confidence' (0.0-1.0). "
                f"No extra text. Use null if unsure."
            ])

            logger.info(f"Codex exec command: {' '.join(cmd)}")

            # Codex execを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1分タイムアウト
            )

            logger.debug(f"Return code: {result.returncode}")
            logger.debug(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"Codex exec failed (code {result.returncode}): {result.stderr}")

            # 出力をパース
            output = result.stdout.strip()

            if not output:
                raise Exception("Codex execの出力が空です")

            # JSONとしてパース
            try:
                data = json.loads(output)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Output: {output}")
                raise Exception(f"JSONパースエラー: {str(e)}")

            category = data.get("category")
            confidence = data.get("confidence", 0.0)

            logger.info(f"分類成功: category={category}, confidence={confidence}")

            return {
                "success": True,
                "category": category,
                "confidence": confidence
            }

        except subprocess.TimeoutExpired:
            logger.error("Codex exec がタイムアウトしました")
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

            if input_file and os.path.exists(input_file.name):
                try:
                    os.unlink(input_file.name)
                except Exception as e:
                    logger.warning(f"Input file削除失敗: {str(e)}")
