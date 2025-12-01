from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import json
import os
import subprocess
import tempfile
import shutil
import glob
import re
import logging

# ロガーの設定
logger = logging.getLogger(__name__)


class OCRService:
    """OCRサービス（YomiToku CLIを使用）"""

    @staticmethod
    def process_receipt(image_path: str) -> Dict:
        """
        レシート画像をOCR処理

        YomiToku CLIを使用してレシート画像を解析します。
        レシート向けに最適化されたオプション（--reading_order left2right）を使用。
        """
        temp_dir = None
        try:
            # 画像ファイルの存在確認
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")

            logger.info(f"OCR処理開始: {image_path}")

            # 一時出力ディレクトリを作成
            temp_dir = tempfile.mkdtemp(prefix="yomitoku_")
            logger.debug(f"一時ディレクトリ作成: {temp_dir}")

            # YomiToku CLI コマンド（レシート向け最適化）
            # --lite: 軽量モデル（高速）
            # -d cpu: CPU推論
            # -f json: JSON出力（構造化データとして扱いやすい）
            # --reading_order left2right: レシート向け（キー:値の段組みレイアウトに有効）
            # --ignore_line_break: 改行を無視して段落内テキストを連結
            cmd = [
                "yomitoku",
                image_path,
                "-f", "json",
                "--lite",
                "-d", "cpu",
                "-o", temp_dir,
                "--reading_order", "left2right",
                "--ignore_line_break"
            ]

            logger.info(f"YomiToku CLI実行: {' '.join(cmd)}")

            # CLIを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分タイムアウト
            )

            if result.returncode != 0:
                logger.error(f"YomiToku CLI失敗: return code={result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                logger.error(f"STDOUT: {result.stdout}")
                raise Exception(f"YomiToku CLI failed (code {result.returncode}): {result.stderr}")

            # 出力ファイルを探す（<stem>_p1.json形式）
            json_files = glob.glob(os.path.join(temp_dir, "*_p1.json"))
            logger.debug(f"一時ディレクトリ内のファイル: {os.listdir(temp_dir)}")

            if not json_files:
                logger.error(f"OCR結果ファイルが見つかりません。出力ディレクトリ: {temp_dir}")
                raise Exception("OCR結果ファイルが見つかりませんでした")

            # JSONファイルを読み込む
            json_path = json_files[0]
            logger.info(f"OCR結果ファイル読み込み: {json_path}")

            with open(json_path, 'r', encoding='utf-8') as f:
                ocr_result = json.load(f)

            logger.debug(f"JSON構造のトップレベルキー: {list(ocr_result.keys())}")

            # テキストを抽出
            raw_text = OCRService._extract_text_from_json(ocr_result)
            logger.info(f"抽出テキスト長: {len(raw_text)} 文字")

            # 構造化データを解析
            parsed_data = OCRService._parse_receipt_data(raw_text, ocr_result)
            logger.info(f"解析結果: store={parsed_data.get('store_name')}, amount={parsed_data.get('total_amount')}")

            return {
                "success": True,
                "raw_text": raw_text,
                "parsed_data": parsed_data,
                "raw_result": json.dumps(ocr_result, ensure_ascii=False, indent=2)
            }

        except subprocess.TimeoutExpired:
            logger.error("OCR処理がタイムアウトしました")
            return {
                "success": False,
                "error": "OCR処理がタイムアウトしました",
                "raw_text": None,
                "parsed_data": None
            }
        except FileNotFoundError as e:
            logger.error(f"ファイルエラー: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": None,
                "parsed_data": None
            }
        except Exception as e:
            logger.exception(f"OCR処理中に予期しないエラーが発生: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": None,
                "parsed_data": None
            }
        finally:
            # 一時ディレクトリをクリーンアップ
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"一時ディレクトリ削除: {temp_dir}")
                except Exception as e:
                    logger.warning(f"一時ディレクトリの削除に失敗: {temp_dir} - {str(e)}")

    @staticmethod
    def _extract_text_from_json(ocr_result: Dict) -> str:
        """
        YomiToku JSON出力からテキストを抽出

        YomiTokuのJSON構造は複数のパターンがあるため、柔軟に対応:
        1. blocks -> lines -> text
        2. lines -> text (直接)
        3. text (単一フィールド)
        """
        text_lines = []

        try:
            # パターン1: blocks -> lines -> text
            if "blocks" in ocr_result:
                logger.debug(f"blocks構造を検出: {len(ocr_result['blocks'])} blocks")
                for block in ocr_result["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            if "text" in line and line["text"]:
                                # <br>タグを除去
                                text = line["text"].replace("<br>", " ").replace("<BR>", " ")
                                text_lines.append(text.strip())

            # パターン2: lines -> text (直接)
            elif "lines" in ocr_result:
                logger.debug(f"lines構造を検出: {len(ocr_result['lines'])} lines")
                for line in ocr_result["lines"]:
                    if "text" in line and line["text"]:
                        text = line["text"].replace("<br>", " ").replace("<BR>", " ")
                        text_lines.append(text.strip())

            # パターン3: text (単一フィールド)
            elif "text" in ocr_result:
                logger.debug("text構造を検出")
                text = ocr_result["text"].replace("<br>", "\n").replace("<BR>", "\n")
                return text.strip()

            # その他: 全てのテキストフィールドを探索
            else:
                logger.warning("既知のJSON構造が見つかりません。全フィールドを探索します")
                text_lines = OCRService._extract_all_text_fields(ocr_result)

            result = "\n".join(text_lines)
            logger.debug(f"テキスト抽出完了: {len(text_lines)} 行, {len(result)} 文字")
            return result

        except Exception as e:
            logger.error(f"テキスト抽出エラー: {str(e)}")
            return ""

    @staticmethod
    def _extract_all_text_fields(data, depth=0, max_depth=10) -> List[str]:
        """
        JSON構造を再帰的に探索してすべてのテキストフィールドを抽出

        Args:
            data: 探索するデータ（dict, list, str, etc）
            depth: 現在の深さ
            max_depth: 最大探索深度

        Returns:
            List[str]: 抽出されたテキストのリスト
        """
        if depth > max_depth:
            return []

        texts = []

        if isinstance(data, dict):
            # "text"キーがあれば優先的に取得
            if "text" in data and isinstance(data["text"], str) and data["text"].strip():
                texts.append(data["text"].strip())
            # 他のキーも再帰的に探索
            for key, value in data.items():
                if key != "text":  # textは既に処理済み
                    texts.extend(OCRService._extract_all_text_fields(value, depth + 1, max_depth))

        elif isinstance(data, list):
            for item in data:
                texts.extend(OCRService._extract_all_text_fields(item, depth + 1, max_depth))

        return texts

    @staticmethod
    def _parse_receipt_data(raw_text: str, ocr_result: Dict) -> Dict:
        """
        レシートデータを解析して構造化情報を抽出

        Args:
            raw_text: 抽出されたテキスト全文
            ocr_result: YomiTokuのJSON出力

        Returns:
            Dict: {
                "store_name": 店舗名,
                "product_name": 商品名,
                "total_amount": 合計金額,
                "date": 日付,
                "items": []
            }
        """
        parsed = {
            "store_name": None,
            "product_name": None,
            "total_amount": None,
            "date": None,
            "items": []
        }

        try:
            lines = raw_text.split('\n')
            logger.debug(f"レシートデータ解析開始: {len(lines)} 行")

            # 1. 店舗名の抽出（最初の数行から推定）
            # レシートは通常、最初に店舗名が表示される
            for i, line in enumerate(lines[:5]):  # 最初の5行を確認
                line = line.strip()
                # 長すぎず短すぎず、数字だけでない行を店舗名候補とする
                if 2 <= len(line) <= 30 and not line.replace(' ', '').isdigit():
                    # 特定のキーワードを含む行はスキップ
                    skip_keywords = ['領収書', 'レシート', 'TEL', '電話', '住所', '〒']
                    if not any(kw in line for kw in skip_keywords):
                        parsed["store_name"] = line
                        logger.debug(f"店舗名を検出: {line}")
                        break

            # 2. 合計金額の抽出
            # レシートでよく使われるパターン
            amount_patterns = [
                r'(?:合計|小計|総計|計|お買上金額|お買上げ金額)[:\s　]*¥?[\s　]*([\d,]+)',
                r'(?:合計|小計|総計|計|お買上金額|お買上げ金額)[:\s　]*([\d,]+)[\s　]*円',
                r'¥[\s　]*([\d,]+)(?:\s|$)',
                r'([\d,]+)[\s　]*円(?:\s*\(税込\))?(?:\s|$)',
            ]

            # 逆順で検索（合計は通常レシートの下部にある）
            for line in reversed(lines):
                for pattern in amount_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').replace('　', '')
                        try:
                            amount = float(amount_str)
                            # 妥当な金額範囲かチェック（1円〜1,000,000円）
                            if 1 <= amount <= 1000000:
                                parsed["total_amount"] = amount
                                logger.debug(f"合計金額を検出: {amount}円 (行: {line})")
                                break
                        except ValueError:
                            continue
                if parsed["total_amount"]:
                    break

            if not parsed["total_amount"]:
                logger.warning("合計金額を検出できませんでした")

            # 3. 日付の抽出
            date_patterns = [
                # YYYY/MM/DD, YYYY-MM-DD
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
                # YYYY年MM月DD日
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                # MM/DD/YYYY
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
                # 令和X年MM月DD日
                r'令和(\d+)年(\d{1,2})月(\d{1,2})日',
                # 平成X年MM月DD日
                r'平成(\d+)年(\d{1,2})月(\d{1,2})日',
            ]

            for line in lines:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        parsed["date"] = match.group(0)
                        logger.debug(f"日付を検出: {parsed['date']} (行: {line})")
                        break
                if parsed["date"]:
                    break

            if not parsed["date"]:
                logger.warning("日付を検出できませんでした")

            # 4. 商品名の生成
            if parsed["store_name"]:
                parsed["product_name"] = f"{parsed['store_name']}での購入"
            else:
                parsed["product_name"] = "レシート購入品"

            logger.debug(f"商品名を生成: {parsed['product_name']}")

            # 5. 明細行の抽出（オプション・将来的な拡張用）
            # 商品名と金額のペアを検出
            item_pattern = r'(.+?)\s+([\d,]+)円?'
            for line in lines:
                # 合計行などをスキップ
                if any(kw in line for kw in ['合計', '小計', '総計', 'お買上', '領収']):
                    continue

                match = re.match(item_pattern, line.strip())
                if match:
                    item_name = match.group(1).strip()
                    item_price_str = match.group(2).replace(',', '')
                    try:
                        item_price = float(item_price_str)
                        if 1 <= item_price <= 100000:  # 妥当な単価範囲
                            parsed["items"].append({
                                "name": item_name,
                                "price": item_price
                            })
                    except ValueError:
                        pass

            if parsed["items"]:
                logger.debug(f"明細行を検出: {len(parsed['items'])} 件")

            logger.info(f"レシートデータ解析完了: store={parsed['store_name']}, amount={parsed['total_amount']}, date={parsed['date']}, items={len(parsed['items'])}")

        except Exception as e:
            logger.error(f"レシートデータ解析エラー: {str(e)}", exc_info=True)

        return parsed
