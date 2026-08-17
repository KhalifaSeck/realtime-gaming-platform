# ============================================================
# main.tf - Ressources Azure de la Brique 1
# ============================================================

# ---------- Locals : valeurs calculées réutilisables ----------
locals {
  # Préfixe standard pour toutes les ressources : "rtgaming-dev"
  name_prefix = "${var.project_name}-${var.environment}"

  # Tags : fusion des tags projet + tag d'environnement
  common_tags = merge(
    var.azure_tags,
    {
      environment = var.environment
    }
  )
}

# ---------- Resource Group ----------
# Le RG contient toutes les ressources Azure de ce projet.
# Suppression du RG = suppression de tout ce qu'il contient.
resource "azurerm_resource_group" "main" {
  name     = "${local.name_prefix}-rg"
  location = var.azure_location
  tags     = local.common_tags
}