# ============================================================
# adls.tf - Azure Data Lake Storage Gen2
#
# Architecture :
#   Storage Account (HNS enabled = ADLS Gen2)
#     ├─ container "raw"          -> données brutes (IGDB, Kafka JSON)
#     ├─ container "curated"      -> Parquet nettoyé par Spark
#     └─ container "checkpoints"  -> Spark Structured Streaming state
# ============================================================

# ---------- Suffixe aléatoire ----------
# Les noms de storage account sont globalement uniques dans TOUT Azure
# (comme les buckets S3). Un suffixe aléatoire évite les collisions.
resource "random_string" "storage_suffix" {
  length  = 6
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# ---------- Storage Account (ADLS Gen2) ----------
# Nom : "rtgamingdevlake<6chars>" (~23 chars, sous les 24 max)
resource "azurerm_storage_account" "lake" {
  name = "${var.project_name}${var.environment}lake${random_string.storage_suffix.result}"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  is_hns_enabled = true

  shared_access_key_enabled = true

  https_traffic_only_enabled = true
  min_tls_version            = "TLS1_2"

  tags = local.common_tags
}

# ---------- Containers ----------
resource "azurerm_storage_container" "raw" {
  name               = "raw"
  storage_account_id = azurerm_storage_account.lake.id
}

resource "azurerm_storage_container" "curated" {
  name               = "curated"
  storage_account_id = azurerm_storage_account.lake.id
}

resource "azurerm_storage_container" "checkpoints" {
  name               = "checkpoints"
  storage_account_id = azurerm_storage_account.lake.id
}