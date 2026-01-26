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

@app.get("/api/rates")
def get_rates(
    currency: str = Query("JPY"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):

    logger.info(f"為替レート取得 API リクエスト開始 - 通貨: {currency}, 期間: {from_date} から {to_date} まで")
    data_list = []

    try:
        # S3バケットからオブジェクト一覧を取得
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            logger.error("S3バケットにオブジェクトが存在しません。")
            return [] # オブジェクトが存在しない場合、空リストを返す

        # オブジェクトを日付順にソート
        sorted_list_objects = sorted(response["Contents"], key=lambda x: x["Key"])

        for list_obj in sorted_list_objects:
            list_obj_key = list_obj["Key"]

            # JSON 以外をスキップ
            if not list_obj_key.endswith(".json"):
                continue

            # S3からJSONデータを取得
            obj = s3_client.get_object(Bucket=bucket_name, Key=list_obj_key)
            data = json.loads(obj["Body"].read().decode("utf-8"))
            target_date = data["date"]

            # 期間フィルタリング
            if from_date and target_date < from_date:
                continue
            if to_date and target_date > to_date:
                continue
            
            # レート計算
            rates = data["rates"]
            usd_jpy = rates.get("JPY")
            if not usd_jpy:
                logger.error(f"USD/JPY レートが存在しません。日付: {target_date}")
                break

            if currency == "JPY":
                # USD/JPY
                val = usd_jpy
            else:
                # 対円レートの計算 (例: EUR/JPY = USD/JPY / USD/EUR)
                usd_xxx = rates.get(currency)
                if usd_jpy and usd_xxx:
                    val = round(usd_jpy / usd_xxx, 2)
                else:
                    logger.error(f"USD/{currency} レートが存在しません。日付: {target_date}")
                    val = None
            
            if val is not None:
                data_list.append({
                    "date": target_date,
                    "rate": val
                })
    except Exception as e:
        logger.exception("S3からのデータ取得中にエラーが発生しました。")
        return {"error": str(e)}

    return data_list

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = Path(__file__).parent / "static" / "index.html"
    return index_path.read_text(encoding="utf-8")
