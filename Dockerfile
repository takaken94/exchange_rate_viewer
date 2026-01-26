# ---------------------------------------
# Base Stage: 共通設定
# ---------------------------------------
FROM python:3.11-slim AS base

# Pythonが.pycファイルを作成しないようにし、標準出力をバッファリングしない設定
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---------------------------------------
# Builder Stage: 依存関係のインストール
# ---------------------------------------
FROM base AS builder

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------
# Development Stage: 開発用
# ---------------------------------------
FROM builder AS development

# 開発・テストに必要なライブラリを追加インストール
COPY requirements_dev.txt .
RUN pip install --no-cache-dir -r requirements_dev.txt

# アプリ本体とテストコードをコピー
COPY ./app ./app
COPY ./tests ./tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

# ---------------------------------------
# Production Stage: 運用（本番）用
# ---------------------------------------
FROM base AS production

# ビルダーからライブラリだけをコピーして軽量化
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリ本体のみをコピー
COPY ./app ./app

# セキュリティのため非rootユーザーを作成して実行
RUN useradd -m appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]