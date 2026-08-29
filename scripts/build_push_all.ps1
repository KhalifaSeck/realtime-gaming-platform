# ============================================================
# Build + tag + push toutes les images custom vers ACR.
# ============================================================

$ErrorActionPreference = "Stop"
$ACR = "rtgamingdevacrmdid1l.azurecr.io"
$TAG = "latest"

$IMAGES = @(
    @{ name = "rtgaming-api";        context = "api" },
    @{ name = "rtgaming-simulator";  context = "simulator" },
    @{ name = "rtgaming-streaming";  context = "streaming" },
    @{ name = "rtgaming-ingestion";  context = "ingestion" },
    @{ name = "rtgaming-sentinel";   context = "sentinel" },
    @{ name = "rtgaming-dashboard";  context = "dashboard" }
)

Write-Host "=== ACR Login ===" -ForegroundColor Cyan
az acr login --name rtgamingdevacrmdid1l

foreach ($img in $IMAGES) {
    $fullTag = "$ACR/$($img.name):$TAG"
    Write-Host "`n=== [$($img.name)] Build ===" -ForegroundColor Cyan
    docker build -t $fullTag "./$($img.context)"

    Write-Host "=== [$($img.name)] Push ===" -ForegroundColor Cyan
    docker push $fullTag
}

Write-Host "`n✅ Toutes les images push sur $ACR" -ForegroundColor Green
Write-Host "Verifie avec : az acr repository list --name rtgamingdevacrmdid1l -o table" -ForegroundColor Yellow