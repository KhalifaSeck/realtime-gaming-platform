# ============================================================
# Variables Terraform - Brique 1 (Azure : RG, ADLS Gen2, AKS)
# Les variables Snowflake seront ajoutées à la Brique 6.
# ============================================================

# ---------- Métadonnées projet ----------
variable "project_name" {
  description = "Nom du projet (préfixe des ressources). 3-10 chars, lowercase alphanumérique."
  type        = string
  default     = "rtgaming"

  validation {
    condition     = can(regex("^[a-z0-9]{3,10}$", var.project_name))
    error_message = "project_name doit être 3-10 caractères alphanumériques minuscules."
  }
}

variable "environment" {
  description = "Environnement (dev, staging, prod). Utilisé dans le naming et les tags."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment doit être : dev, staging ou prod."
  }
}

# ---------- Azure ----------
variable "azure_subscription_id" {
  description = "Subscription ID Azure (visible via 'az account show --query id -o tsv')."
  type        = string
  # Pas de default : à fournir dans terraform.tfvars
}

variable "azure_location" {
  description = "Région Azure pour les ressources."
  type        = string
  default     = "westeurope"
}

variable "azure_tags" {
  description = "Tags communs appliqués à toutes les ressources Azure (cost tracking, gouvernance)."
  type        = map(string)
  default = {
    project    = "realtime-gaming-platform"
    managed_by = "terraform"
    owner      = "khalifa"
  }
}