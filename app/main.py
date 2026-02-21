from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
from typing import Optional
import os
import sys
import logging
from app.logging_config import setup_logging
import boto3
from datetime import datetime, timedelta
import time

# ロガーの設定
logger = logging.getLogger(__name__)
setup_logging()

# 環境変数の取得
bucket_name = os.getenv("S3_BUCKET_NAME")
if not bucket_name:
    logger.error("環境変数: S3_BUCKET_NAME が設定されていません。")
    sys.exit(1)
prefix = os.getenv("S3_PREFIX")
if not prefix:
    logger.error("環境変数: S3_PREFIX が設定されていません。")
    sys.exit(1)

# Athenaの設定
ATHENA_DB = "default" # Athenaのデータベース名
ATHENA_OUTPUT_S3 = f"s3://{bucket_name}/athena-results/" # クエリ結果の保存先

# FastAPI アプリケーションの作成
app = FastAPI()
if not app:
    logger.error("FastAPI アプリケーションの作成に失敗しました。")
    sys.exit(1)

# S3クライアントの作成
s3_client = boto3.client("s3")
if not s3_client:
    logger.error("S3クライアントの作成に失敗しました。")
    sys.exit(1)

# Athenaクライアントの作成
athena_client = boto3.client("athena")
if not athena_client:
    logger.error("Athenaクライアントの作成に失敗しました。")
    sys.exit(1)

@app.get("/api/rates")
def get_rates(
    currency: str = Query("USD"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):

    logger.info(f"為替レート取得 API リクエスト開始 - 通貨: {currency}, 期間: {from_date} から {to_date} まで")

    # 開始日と終了日
    try:
        start_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.now() - timedelta(days=30) # from_date が未指定の場合、直近30日分
        end_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
    except ValueError:
        return {"error": "日付形式は YYYY-MM-DD で指定してください。"}

    # 年/月 のリストを作成 (例: ["year=2026/month=01/", "year=2026/month=02/"])
    prefixes_to_scan = []
    current_scan_dt = start_dt.replace(day=1)
    while current_scan_dt <= end_dt:
        partition_path = f"{prefix}/year={current_scan_dt.year}/month={current_scan_dt.month:02d}/"
        prefixes_to_scan.append(partition_path)
        # 翌月の1日へ移動
        if current_scan_dt.month == 12:
            current_scan_dt = current_scan_dt.replace(year=current_scan_dt.year + 1, month=1)
        else:
            current_scan_dt = current_scan_dt.replace(month=current_scan_dt.month + 1)

    data_list = []
    # JSONLファイル名用にハイフンを除去 (例: "2026-01-22" -> "20260122")
    start_dt_num = start_dt.strftime("%Y%m%d")
    end_dt_num = end_dt.strftime("%Y%m%d")

    try:
        for p in prefixes_to_scan:
            logger.info(f"Scanning S3 Prefix: {p}")
            # S3バケットからオブジェクト一覧を取得
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=p)
            if "Contents" not in response:
                continue

            for obj_meta in response["Contents"]:
                key = obj_meta["Key"]
                # JSONLファイルのみ処理
                if not key.endswith(".jsonl"):
                    continue

                # JSONLファイル名から日付抽出 (rates_20260220.jsonl -> 20260220)
                filename = os.path.basename(key)
                date_part = "".join(filter(str.isdigit, filename))

                # 日付範囲外ならスキップ (S3 Keyレベルでの判定)
                if start_dt_num and date_part < start_dt_num:
                    continue
                if end_dt_num and date_part > end_dt_num:
                    continue

                # 合致したファイルの内容を読み込み
                obj = s3_client.get_object(Bucket=bucket_name, Key=key)
                lines = obj["Body"].read().decode("utf-8").splitlines()

                for line in lines:
                    if not line.strip():
                        continue

                    # JSONLファイルの各行をJSONとしてパース
                    record = json.loads(line)
                    target_date = record.get("base_date")
                    # 指定された通貨のレートのみ抽出
                    if record.get("currency") == currency:
                        data_list.append({
                            "date": target_date,
                            "rate": record.get("rate")
                        })

    except Exception as e:
        logger.exception("S3からのデータ取得中にエラーが発生しました。")
        return {"error": str(e)}

    # データの並び替え (日付順)
    data_list.sort(key=lambda x: x["date"])
    return data_list

@app.get("/api/athena-rates")
def get_rates_athena(
    currency: str = Query("USD"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    # 開始日と終了日
    try:
        start_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.now() - timedelta(days=30) # from_date が未指定の場合、直近30日分
        end_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
    except ValueError:
        return {"error": "日付形式は YYYY-MM-DD で指定してください。"}

    # SQLの構築 (バリデーション済みの想定)
    query = f"""
    SELECT base_date, rate
    FROM exchange_rates
    WHERE currency = '{currency}'
    AND base_date >= date '{start_dt.strftime("%Y-%m-%d")}'
    AND base_date <= date '{end_dt.strftime("%Y-%m-%d")}'
    ORDER BY base_date ASC;
    """

    try:
        # 1. クエリ実行開始
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': ATHENA_DB},
            ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_S3}
        )
        query_execution_id = response['QueryExecutionId']

        # 2. 完了を待機（ポーリング）
        while True:
            status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = status['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(0.5)

        if state != 'SUCCEEDED':
            # エラー詳細を取得
            error_msg = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise Exception(f"Athena query failed: {state} - {error_msg}")

        # 3. 結果の取得
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        data_list = []
        rows = results['ResultSet']['Rows']
        
        # 0行目はカラム名なのでスキップ
        for row in rows[1:]:
            # Data[0]がbase_date, Data[1]がrate
            data_list.append({
                "date": row['Data'][0].get('VarCharValue'),
                "rate": float(row['Data'][1].get('VarCharValue', 0))
            })
            
        return data_list

    except Exception as e:
        logger.exception("Athena実行エラー")
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = Path(__file__).parent / "static" / "index.html"

    if not index_path.exists():
        return HTMLResponse(content="<h1>Index file not found</h1>", status_code=404)
    return index_path.read_text(encoding="utf-8")

@app.get("/benchmark", response_class=HTMLResponse)
def read_benchmark():
    benchmark_path = Path(__file__).parent / "static" / "benchmark.html"

    if not benchmark_path.exists():
        return HTMLResponse(content="<h1>Benchmark file not found</h1>", status_code=404)
    return benchmark_path.read_text(encoding="utf-8")