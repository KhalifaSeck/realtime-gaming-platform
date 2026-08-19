# ============================================================
# main.tf - Ressources Snowflake (Brique 6)
#
# Cree :
#   - Database : RTGAMING_DEV
#   - Schemas  : RAW, STAGING, ANALYTICS (medallion)
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


resource "snowflake_schema" "analytics" {
  database = snowflake_database.main.name
  name     = "ANALYTICS"
  comment  = "Aggregated analytics tables (Spark streaming + batch outputs)"
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
    snowflake_schema.analytics,
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

# ============================================================
# File Format + External Stage vers ADLS Gen2
# ============================================================

resource "snowflake_file_format" "parquet_snappy" {
  database    = snowflake_database.main.name
  schema      = snowflake_schema.raw.name
  name        = "PARQUET_SNAPPY"
  format_type = "PARQUET"
  comment     = "Parquet with Snappy compression (matches Spark output)"
}

resource "snowflake_stage" "adls_raw" {
  database = snowflake_database.main.name
  schema   = snowflake_schema.raw.name
  name     = "ADLS_RAW"
  comment  = "External stage pointing to ADLS Gen2 raw container"

  # Note : URL utilise .blob.core.windows.net (API Blob) meme si HNS active.
  # C'est le format supporte par Snowflake CREATE STAGE.
  url         = "azure://${var.adls_account_name}.blob.core.windows.net/${var.adls_container_raw}"
  credentials = "AZURE_SAS_TOKEN='${var.adls_sas_token}'"
  file_format = "FORMAT_NAME = ${snowflake_database.main.name}.${snowflake_schema.raw.name}.${snowflake_file_format.parquet_snappy.name}"
}