# ============================================================
# main.tf - Ressources Snowflake (Brique 6)
#
# Cree :
#   - Database : RTGAMING_DEV
#   - Schemas  : RAW, STAGING, MARTS (medallion)
#   - Role     : RTGAMING_DEV_ROLE (least-privilege pour dbt/apps)
#   - Grants   : USAGE sur DB/WH, tout sur schemas (existants + futurs)
#   - Attribution du role a l'user Terraform
# ============================================================

locals {
  db_name   = "${upper(var.project_name)}_${upper(var.environment)}" # RTGAMING_DEV
  role_name = "${local.db_name}_ROLE"                                # RTGAMING_DEV_ROLE
}

# ---------- Database ----------
resource "snowflake_database" "main" {
  name    = local.db_name
  comment = "Realtime gaming platform data (${var.environment})"
}

# ---------- Schemas (Medallion) ----------
resource "snowflake_schema" "raw" {
  database = snowflake_database.main.name
  name     = "RAW"
  comment  = "Raw data ingested from ADLS Gen2 (COPY INTO)"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.main.name
  name     = "STAGING"
  comment  = "Cleaned and typed tables (dbt staging models)"
}

resource "snowflake_schema" "marts" {
  database = snowflake_database.main.name
  name     = "MARTS"
  comment  = "Business-ready analytics tables (dbt marts, Power BI)"
}

# ---------- Role custom ----------
resource "snowflake_account_role" "pipeline" {
  name    = local.role_name
  comment = "Pipeline role for ingestion + dbt + apps (least-privilege)"
}

# ---------- Grants ----------
# USAGE sur la database
resource "snowflake_grant_privileges_to_account_role" "db_usage" {
  account_role_name = snowflake_account_role.pipeline.name
  privileges        = ["USAGE"]

  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.main.name
  }
}

# USAGE + OPERATE sur le warehouse (executer des queries)
resource "snowflake_grant_privileges_to_account_role" "wh_usage" {
  account_role_name = snowflake_account_role.pipeline.name
  privileges        = ["USAGE", "OPERATE"]

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.snowflake_warehouse
  }
}

# Perms sur tous les schemas existants
resource "snowflake_grant_privileges_to_account_role" "schemas_all" {
  account_role_name = snowflake_account_role.pipeline.name
  privileges = [
    "USAGE",
    "CREATE TABLE",
    "CREATE VIEW",
    "CREATE STAGE",
    "CREATE FILE FORMAT",
  ]

  on_schema {
    all_schemas_in_database = snowflake_database.main.name
  }

  depends_on = [
    snowflake_schema.raw,
    snowflake_schema.staging,
    snowflake_schema.marts,
  ]
}

# Meme perms sur les futurs schemas (auto-grant)
resource "snowflake_grant_privileges_to_account_role" "schemas_future" {
  account_role_name = snowflake_account_role.pipeline.name
  privileges = [
    "USAGE",
    "CREATE TABLE",
    "CREATE VIEW",
    "CREATE STAGE",
    "CREATE FILE FORMAT",
  ]

  on_schema {
    future_schemas_in_database = snowflake_database.main.name
  }
}

# Attribuer le role a l'user Terraform
resource "snowflake_grant_account_role" "to_user" {
  role_name = snowflake_account_role.pipeline.name
  user_name = var.snowflake_user
}