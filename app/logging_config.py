import logging
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # すでに handler があれば二重登録しない
    if logger.handlers:
        return

    # --- JST 変換の設定 ---
    # formatter が時刻を生成する際に使用する関数を定義
    def jst_converter(*args):
        return datetime.now(timezone(timedelta(hours=+9))).timetuple()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    # UTC を JST に差し替え
    formatter.converter = jst_converter

    # コンソール出力（stdout）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイル出力（ローカル環境のみ）
    # Lambda 実行判定
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    if not is_lambda:
        # ローカルのみファイル出力
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / "app.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
