from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# .envファイルを探して読み込む
# find_dotenv()は親ディレクトリを遡って.envファイルを探す
# usecwd=Trueで、カレントディレクトリから探し始める
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    # カレントディレクトリから見つからない場合、このファイルの位置から探す
    # backend/app/config.py から見て ../../.env (プロジェクトルート)
    current_dir = Path(__file__).resolve().parent
    project_root_env = current_dir.parent.parent / ".env"
    if project_root_env.exists():
        dotenv_path = str(project_root_env)

# .envファイルを環境変数として読み込む
if dotenv_path:
    load_dotenv(dotenv_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding='utf-8'
    )

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "ai_kakeibo"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    UPLOAD_DIR: str = "./uploads/receipts"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp"

    # OCR
    OCR_MAX_WORKERS: int = 2

    # AI
    CLAUDE_CLI_PATH: str = "claude"
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"

    # Application
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
