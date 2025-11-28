import os
import uuid
from datetime import datetime
from PIL import Image
from typing import Tuple
from app.config import settings


class ImageService:
    """画像処理サービス"""

    @staticmethod
    def compress_image(image_path: str, max_size: Tuple[int, int] = (1920, 1920), quality: int = 85) -> None:
        """画像を圧縮"""
        try:
            with Image.open(image_path) as img:
                # EXIF情報に基づいて回転
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    orientation = exif.get(0x0112)
                    if orientation:
                        rotations = {
                            3: 180,
                            6: 270,
                            8: 90
                        }
                        if orientation in rotations:
                            img = img.rotate(rotations[orientation], expand=True)

                # リサイズ（アスペクト比を保持）
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # RGB変換（PNGの透過を処理）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                # 保存
                img.save(image_path, 'JPEG', quality=quality, optimize=True)
        except Exception as e:
            raise Exception(f"画像圧縮エラー: {str(e)}")

    @staticmethod
    def save_receipt_image(file_data: bytes, original_filename: str) -> Tuple[str, str]:
        """レシート画像を保存"""
        # ユニークなファイル名を生成
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise ValueError("サポートされていないファイル形式です")

        # 日付ベースのディレクトリ構造
        date_path = datetime.now().strftime("%Y/%m/%d")
        full_dir = os.path.join(settings.UPLOAD_DIR, date_path)
        os.makedirs(full_dir, exist_ok=True)

        # ファイル名生成
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(full_dir, stored_filename)

        # ファイル保存
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # 圧縮
        ImageService.compress_image(file_path)

        # 相対パスを返す
        relative_path = os.path.join(date_path, stored_filename)
        return file_path, relative_path

    @staticmethod
    def get_full_path(relative_path: str) -> str:
        """相対パスから絶対パスを取得"""
        return os.path.join(settings.UPLOAD_DIR, relative_path)

    @staticmethod
    def delete_image(file_path: str) -> bool:
        """画像を削除"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
