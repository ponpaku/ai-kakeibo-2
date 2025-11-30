from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import json
import cv2
import numpy as np


class OCRService:
    """OCRサービス（YomiTokuを使用）"""

    @staticmethod
    def process_receipt(image_path: str) -> Dict:
        """レシート画像をOCR処理"""
        try:
            from yomitoku import DocumentAnalyzer

            # CPUで処理するように設定
            analyzer = DocumentAnalyzer(
                configs={
                    "enable_all": True,
                },
                visualize=False,
                device="cpu"  # CPUを使用
            )

            # 画像を読み込む（OpenCVでnumpy配列として）
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"画像を読み込めませんでした: {image_path}")

            # BGRからRGBに変換（yomitokuはRGB形式を期待）
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # OCR実行（numpy配列を渡す）
            result = analyzer(image_rgb)

            # 結果を解析
            parsed_data = OCRService._parse_ocr_result(result)

            return {
                "success": True,
                "raw_text": OCRService._extract_text(result),
                "parsed_data": parsed_data,
                "raw_result": json.dumps(result, ensure_ascii=False, default=str)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_text": None,
                "parsed_data": None
            }

    @staticmethod
    def _extract_text(result) -> str:
        """OCR結果からテキストを抽出"""
        try:
            text_lines = []
            if hasattr(result, 'text_result') and result.text_result:
                for line in result.text_result:
                    if hasattr(line, 'text'):
                        text_lines.append(line.text)
            return "\n".join(text_lines)
        except Exception:
            return str(result)

    @staticmethod
    def _parse_ocr_result(result) -> Dict:
        """OCR結果から構造化データを抽出"""
        parsed = {
            "store_name": None,
            "product_name": None,
            "total_amount": None,
            "date": None,
            "items": []
        }

        try:
            # YomiTokuの結果から情報を抽出
            # 店舗名の抽出
            if hasattr(result, 'text_result') and result.text_result:
                # 最初の数行から店舗名を推定
                if len(result.text_result) > 0:
                    parsed["store_name"] = result.text_result[0].text if hasattr(result.text_result[0], 'text') else None

            # テキストから金額と日付を抽出（正規表現を使用）
            import re
            full_text = OCRService._extract_text(result)

            # 合計金額の抽出（¥マークや「合計」「計」などのキーワードから）
            amount_patterns = [
                r'合計[:\s]*¥?[\s]*([\d,]+)',
                r'計[:\s]*¥?[\s]*([\d,]+)',
                r'¥[\s]*([\d,]+)',
                r'([\d,]+)円'
            ]
            for pattern in amount_patterns:
                match = re.search(pattern, full_text)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        parsed["total_amount"] = float(amount_str)
                        break
                    except ValueError:
                        continue

            # 日付の抽出
            date_patterns = [
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
                r'令和(\d+)年(\d{1,2})月(\d{1,2})日',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, full_text)
                if match:
                    parsed["date"] = match.group(0)
                    break

            # 商品名の抽出（店舗名がある場合は「{店舗名}での購入」、ない場合は「レシート購入品」）
            if parsed["store_name"]:
                parsed["product_name"] = f"{parsed['store_name']}での購入"
            else:
                parsed["product_name"] = "レシート購入品"

        except Exception as e:
            print(f"OCR解析エラー: {str(e)}")

        return parsed
