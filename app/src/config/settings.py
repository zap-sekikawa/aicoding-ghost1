from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # リポジトリ設定
    USE_MOCK: bool = True  # デフォルトはモック環境
    EXTERNAL_API_BASE_URL: Optional[str] = None  # 本番環境用のAPI URL
    
    # その他の設定
    APP_NAME: str = "Fortune API"
    APP_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# グローバルなインスタンス
settings = Settings()
