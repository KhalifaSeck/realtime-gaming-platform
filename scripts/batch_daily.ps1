# ============================================================
# Batch daily pipeline (equivalent DAG batch_pipeline_daily)
# Executed by Windows Task Scheduler (or manually).
# ============================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\Users\lifas\OneDrive\Documents\Data Engineering\realtime-gaming-platform"

function Log-Step($msg) {
    Write-Host "`n===== [$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg =====" -ForegroundColor Cyan
}

try {
    # 1. IGDB ingestion
    Log-Step "1/5 - IGDB ingestion"
    Set-Location "$ProjectRoot\ingestion"
    python -m src.main --source igdb --limit 10000

    # 2. SteamSpy ingestion (--enrich-limit 500 pour ~3 min)
    Log-Step "2/5 - SteamSpy ingestion"
    python -m src.main --source steamspy --enrich-limit 500

    # 3. COPY INTO batch
    Log-Step "3/5 - COPY INTO batch (RAW.IGDB_GAMES + RAW.STEAMSPY_GAMES)"
    Set-Location "$ProjectRoot\snowflake"
    python -m ops.runner sql/copy/02_batch.sql

    # 4. COPY INTO streaming
    Log-Step "4/5 - COPY INTO streaming (RAW.STREAM_*)"
    python -m ops.runner sql/copy/03_streaming_raw_events.sql

    # 5. dbt run
    Log-Step "5/5 - dbt run staging + marts"
    Set-Location "$ProjectRoot\gaming_dbt"
    dbt run --select staging marts

    Log-Step "SUCCESS - Pipeline complete"
    exit 0
}
catch {
    Log-Step "FAILED - $($_.Exception.Message)"
    exit 1
}