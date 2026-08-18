"""
Writer : liste de dicts -> Parquet en memoire -> upload direct ADLS Gen2.
"""
from __future__ import annotations

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
    return DataLakeServiceClient(
        account_url=account_url,
        credential=DefaultAzureCredential(),
    )


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
    service = _adls_client()
    fs = service.get_file_system_client(settings.adls_container_raw)
    file_client = fs.get_file_client(remote_path)
    file_client.upload_data(buffer, overwrite=True)

    log.info(
        "writer.adls.done",
        container=settings.adls_container_raw,
        path=remote_path,
        rows=len(df),
        size_kb=size_kb,
    )
    return remote_path