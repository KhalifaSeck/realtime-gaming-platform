output "database_name" {
  description = "Nom de la Snowflake database creee."
  value       = snowflake_database.main.name
}

output "schemas" {
  description = "Noms des schemas (medallion : RAW, STAGING, ANALYTICS)."
  value = [
    snowflake_schema.raw.name,
    snowflake_schema.staging.name,
    snowflake_schema.analytics.name,
  ]
}

output "pipeline_role_name" {
  description = "Role Snowflake dedie au pipeline (dbt, apps)."
  value       = snowflake_account_role.pipeline.name
}

output "adls_stage_fqn" {
  description = "FQN du stage externe vers ADLS."
  value       = "${snowflake_database.main.name}.${snowflake_schema.raw.name}.${snowflake_stage.adls_raw.name}"
}

output "parquet_file_format_fqn" {
  description = "FQN du file format Parquet."
  value       = "${snowflake_database.main.name}.${snowflake_schema.raw.name}.${snowflake_file_format.parquet_snappy.name}"
}