# ============================================================
# outputs.tf - Valeurs exposées après 'terraform apply'
# ============================================================

# ---------- Resource Group ----------
output "resource_group_name" {
  description = "Nom du Resource Group Azure."
  value       = azurerm_resource_group.main.name
}

# ---------- ADLS Gen2 ----------
output "adls_account_name" {
  description = "Nom du Storage Account ADLS Gen2."
  value       = azurerm_storage_account.lake.name
}

output "adls_primary_dfs_endpoint" {
  description = "Endpoint DFS de l'ADLS (utilisé par Spark et Snowflake)."
  value       = azurerm_storage_account.lake.primary_dfs_endpoint
}

output "adls_containers" {
  description = "Noms des containers créés dans le lake."
  value = [
    azurerm_storage_container.raw.name,
    azurerm_storage_container.curated.name,
    azurerm_storage_container.checkpoints.name,
  ]
}