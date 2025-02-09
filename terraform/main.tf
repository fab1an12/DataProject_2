module "telegram_api" {
  source             = "./modules/telegram_api"
  project_id         = var.project_id
  telegram_bot_token = var.telegram_bot_token
  region             = var.region
  repository_name    = var.repository_name
  job_name           = var.job_name
  }

# module "ia-agent" {
#   source             = "./modules/ia-agent"
#   project_id         = var.project_id
#   environment        = var.environment
#   region             = var.region
#   cloud_function_runtime = var.cloud_function_runtime
#   openai_api_key     = var.openai_api_key
#   langchain_api_key  = var.langchain_api_key
#   langchain_tracing = var.langchain_tracing
# }