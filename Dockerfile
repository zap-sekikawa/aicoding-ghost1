#====================================================================
# [Dockerfile] サンプル
#====================================================================
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 依存ライブラリ例(lxml等で必要なシステムパッケージ)
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# プロジェクトをコピー
COPY . /app

# Pythonパッケージをインストール
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ポート公開
EXPOSE 8000

# コンテナ起動時のコマンド
CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
