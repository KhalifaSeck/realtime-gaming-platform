# ============================================================
# Variables Terraform - Snowflake module (Brique 6)
# ============================================================

# ---------- Metadonnees projet ----------
variable "project_name" {
  description = "Nom du projet (prefixe des ressources)."
  type        = string
  default     = "rtgaming"

  validation {
    condition     = can(regex("^[a-z0-9]{3,10}$", var.project_name))
    error_message = "project_name doit etre 3-10 caracteres alphanumeriques minuscules."
  }
}

variable "environment" {
  description = "Environnement (dev, staging, prod)."
  type        = string
  default     = "dev"
}

# ---------- Snowflake credentials ----------
variable "snowflake_organization_name" {
  description = "Organization name Snowflake (1ere partie de l'URL Snowsight)."
  type        = string
}

variable "snowflake_account_name" {
  description = "Account name Snowflake (2eme partie de l'URL)."
  type        = string
}

variable "snowflake_user" {
  description = "User Snowflake (ex: BAKISSECK96)."
  type        = string
}

variable "snowflake_password" {
  description = "Password Snowflake."
  type        = string
  sensitive   = true
}

variable "snowflake_role" {
  description = "Role Snowflake utilise par Terraform."
  type        = string
  default     = "ACCOUNTADMIN"
}

variable "snowflake_warehouse" {
  description = "Warehouse Snowflake par defaut."
  type        = string
  default     = "COMPUTE_WH"
}