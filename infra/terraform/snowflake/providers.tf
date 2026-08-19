provider "snowflake" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
  password          = var.snowflake_password
  role              = var.snowflake_role
  warehouse         = var.snowflake_warehouse
  authenticator     = "SNOWFLAKE"

  preview_features_enabled = [
    "snowflake_file_format_resource",
    "snowflake_stage_resource",
  ]
}