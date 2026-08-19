output "database_name" {
  description = "Nom de la Snowflake database creee."
  value       = snowflake_database.main.name
}

output "schemas" {
  description = "Noms des schemas (medallion : RAW, STAGING, MARTS)."
  value = [
    snowflake_schema.raw.name,
    snowflake_schema.staging.name,
    snowflake_schema.marts.name,
  ]
}

output "pipeline_role_name" {
  description = "Role Snowflake dedie au pipeline (dbt, apps)."
  value       = snowflake_account_role.pipeline.name
}