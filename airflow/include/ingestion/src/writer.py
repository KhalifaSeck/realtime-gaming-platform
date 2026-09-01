"""
Writer : liste de dicts -> Parquet en memoire -> upload direct ADLS Gen2.

Auth ADLS :
  - Si env ADLS_ACCOUNT_KEY est set -> SharedKeyCredential (container-friendly)
  - Sinon -> DefaultAzureCredential (utilise 'az login' en dev host)
"""
from __future__ import annotations

import os
from datetime import date
from io import BytesIO
from typing import Any

import pandas as pd
import structlog
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from config.settings import get_settings

log = structlog.get_logger()


def _adls_client() -> DataLakeServiceClient:
    settings = get_settings()
    account_url = f"https://{settings.adls_account_name}.dfs.core.windows.net"
    account_key = os.environ.get("ADLS_ACCOUNT_KEY")
    if account_key:
        return DataLakeServiceClient(account_url=account_url, credential=account_key)
    return DataLakeServiceClient(
        account_url=account_url,
        credential=DefaultAzureCredential(),
    )


def _upload_to_adls(local_path, source, ingest_date):
    pass  # unused (kept for compat)


def write_parquet(
    records: list[dict[str, Any]],
    source: str,
    ingest_date: date | None = None,
) -> str:
    ingest_date = ingest_date or date.today()

    if not records:
        log.warning("writer.empty", source=source)
        return ""

    df = pd.DataFrame(records)
    buffer = BytesIO()
    df.to_parquet(buffer, engine="pyarrow", compression="snappy", index=False)
    buffer.seek(0)
    size_kb = buffer.getbuffer().nbytes // 1024

    settings = get_settings()
    remote_path = f"{source}/date={ingest_date.isoformat()}/{source}.parquet"
    fs = _adls_client().get_file_system_client(settings.adls_container_raw)
    fs.get_file_client(remote_path).upload_data(buffer, overwrite=True)

    log.info(
        "writer.adls.done",
        container=settings.adls_container_raw,
        path=remote_path,
        rows=len(df),
        size_kb=size_kb,
    )
    return remote_path