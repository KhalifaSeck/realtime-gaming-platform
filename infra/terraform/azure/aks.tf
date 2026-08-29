# ============================================================
# aks.tf - AKS cluster + ACR (Azure Container Registry)
#
# Cost estimate (Canada Central, single node B2s) :
#   AKS control plane   : FREE (SKU Free)
#   1x Standard_B2s     : ~30 CAD/month
#   ACR Basic           : ~5 CAD/month
#   TOTAL               : ~35 CAD/month if left running 24/7
#
# To stop bleeding costs :
#   az aks stop --name rtgaming-dev-aks --resource-group rtgaming-dev-rg
# To restart :
#   az aks start ...
# Full teardown (destructive) :
#   terraform destroy -target=azurerm_kubernetes_cluster.main
#                     -target=azurerm_container_registry.main
# ============================================================

# ---------- Container Registry ----------
resource "random_string" "acr_suffix" {
  length  = 6
  lower   = true
  upper   = false
  numeric = true
  special = false
}

resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}${var.environment}acr${random_string.acr_suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.common_tags
}

# ---------- AKS ----------
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${local.name_prefix}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${local.name_prefix}-aks"
  sku_tier            = "Free"

  default_node_pool {
    name       = "system"
    node_count = 1
    vm_size    = "Standard_B2s_v2"

    os_disk_size_gb = 30
    type            = "VirtualMachineScaleSets"

    node_labels = {
      "role" = "system"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
  }

  role_based_access_control_enabled = true

  tags = local.common_tags
}

# ---------- AKS <-> ACR : rôle AcrPull ----------
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                            = azurerm_container_registry.main.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}

# ---------- AKS -> ADLS : rôle Storage Blob Data Contributor ----------
resource "azurerm_role_assignment" "aks_adls_contributor" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# ---------- Outputs ----------
output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "aks_resource_group" {
  value = azurerm_resource_group.main.name
}

output "aks_get_credentials_cmd" {
  description = "Run this to configure kubectl."
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.main.name} --overwrite-existing"
}

output "acr_name" {
  value = azurerm_container_registry.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}