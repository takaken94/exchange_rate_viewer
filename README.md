# Exchange Rate Viewer 為替レート可視化

## 概要
Amazon S3 に蓄積された為替レートを表示する Webシステム<br>

### 背景・目的
外部 API から取得して、S3 に蓄積した為替レートを、「期間指定で可視化する」Webシステムを想定し、
Webフレームワークの FastAPI を利用して実装しました。

## システム構成
[S3] → [FastAPI] → [Browser]

## 使用技術
- **言語**: Python 3.11
- **ライブラリ**: FastAPI、uvicorn、boto3
<!--
- **基盤**: AWS (Fargate、S3)
-->

## 機能
- **データ取得**: Amazon S3 バケットから JSON形式の為替レートを取得
- **API**: REST API（パラメータ: 通貨コード、日付from、日付to）
```
http://localhost:8000/api/rates?currency=JPY&from_date=2026-01-26&to_date=2026-01-26
```
- **データ表示**: Web ブラウザで為替レートをグラフ表示

## 実行方法
### 開発環境
- **OS**: Windows 11 + WSL2 (Ubuntu)
- **環境構成**: Docker
- **認証**: aws sso login により認証済みであること

### ローカル実行
プロジェクトルートにて以下のコマンドを実行します。

```bash
# SSO login
aws sso login

# Docker コンテナの起動
docker compose up
```

```
user_name@host_name:~/work/exchange_rate_viewer$ docker compose up
WARN[0000] No services to build
Attaching to app-1
app-1  | INFO:     Will watch for changes in these directories: ['/app']
app-1  | INFO:     Uvicorn running on http://0.0.0.0:80 (Press CTRL+C to quit)
app-1  | INFO:     Started reloader process [1] using WatchFiles
app-1  | INFO:     Started server process [8]
app-1  | INFO:     Waiting for application startup.
app-1  | INFO:     Application startup complete.
```

「Application startup complete.」が表示されたら、Webブラウザで http://localhost:8000 にアクセスしてください。

![index.html](doc/exchange_rate_viewer.jpg)

APIドキュメントは http://localhost:8000/docs にて確認できます。

![Swagger UI](doc/swagger_ui.jpg)


### テスト
pytest を使用して、テストを実行します。

```bash
# 起動中のコンテナで実行する場合
docker compose exec app pytest -v

# 新しくコンテナを起動して実行する場合
docker compose run --rm app pytest -v
```

<!--
### テスト結果
```plaintext
```
-->

<!--
## 運用
以下は Fargate 上での稼働状況です。
-->
