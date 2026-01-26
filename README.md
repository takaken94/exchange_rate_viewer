# Exchange Rate Viewer 為替レート可視化

## 概要
Amazon S3 に蓄積された為替レートを表示する Webシステム<br>

<!--
## システム構成
- **実行環境**: AWS Fargate
-->

## 使用技術
- **言語**: Python 3.11
- **ライブラリ**: FastAPI、uvicorn、boto3
<!--
- **基盤**: AWS (Fargate、S3)
-->

## 機能
- **データ取得**: Amazon S3 バケットから JSON形式の為替レートを取得
- **API**: REST API（パラメータ: 通貨コード、日付from、日付to）
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
