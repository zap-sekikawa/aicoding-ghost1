from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import settings
from .endpoints.fortune import router as fortune_router
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    アプリケーション全体のロギング設定
    """
    # ロガーの設定
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # フォーマッターの作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラーの設定（ローテーション付き）
    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # FastAPIのデフォルトロガーの設定
    logging.getLogger("fastapi").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)

def create_app() -> FastAPI:
    """
    FastAPIアプリケーションを作成する
    
    Returns:
        FastAPI: 設定済みのFastAPIアプリケーション
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="運勢API",
    )

    # CORSミドルウェアの設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では適切に制限する
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ルーターの登録
    app.include_router(fortune_router, prefix="/api/v1", tags=["fortune"])

    @app.get("/health")
    def health_check():
        """ヘルスチェックエンドポイント"""
        return {"status": "healthy"}

    return app

# ロギング設定の初期化
setup_logging()
logger = logging.getLogger(__name__)

app = create_app()
logger.info(f"アプリケーション起動: {settings.APP_NAME} v{settings.APP_VERSION}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開発時のみTrue
        log_level="info"
    )
