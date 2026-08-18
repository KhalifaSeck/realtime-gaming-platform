"""
Sink ADLS Gen2 : ecrit chaque batch aggregate en Parquet.

Auth : account key (env ADLS_ACCOUNT_KEY). Simple pour dev.
En AKS : bascule vers Managed Identity via DefaultAzureCredential.

Path : {container}/streaming/{topic}/date=YYYY-MM-DD/batch_{id}_{ts_ms}.parquet
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Callable

from azure.storage.filedatalake import DataLakeServiceClient
from pyspark.sql import DataFrame

ADLS_ACCOUNT = os.environ.get("ADLS_ACCOUNT_NAME")
ADLS_KEY = os.environ.get("ADLS_ACCOUNT_KEY")
ADLS_CONTAINER = os.environ.get("ADLS_CONTAINER_RAW", "raw")


def _adls_client() -> DataLakeServiceClient:
    return DataLakeServiceClient(
        account_url=f"https://{ADLS_ACCOUNT}.dfs.core.windows.net",
        credential=ADLS_KEY,
    )


def make_writer(topic: str) -> Callable:
    def _write(batch_df: DataFrame, batch_id: int) -> None:
        if not ADLS_ACCOUNT or not ADLS_KEY:
            print(f"[adls_sink] skip batch {batch_id}: ADLS_ACCOUNT_NAME/KEY not set")
            return

        pdf = batch_df.toPandas()
        if pdf.empty:
            return

        buffer = BytesIO()
        pdf.to_parquet(buffer, engine="pyarrow", compression="snappy", index=False)
        buffer.seek(0)

        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y-%m-%d")
        ts_ms = int(now.timestamp() * 1000)
        remote_path = f"streaming/{topic}/date={date_part}/batch_{batch_id}_{ts_ms}.parquet"

        fs = _adls_client().get_file_system_client(ADLS_CONTAINER)
        fs.get_file_client(remote_path).upload_data(buffer, overwrite=True)

        print(f"[adls_sink] batch {batch_id} -> {remote_path} ({len(pdf)} rows)")

    return _write