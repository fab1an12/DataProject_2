# module "telegram_api" {
#   source             = "./modules/telegram_api"
#   project_id         = var.project_id
#   telegram_bot_token = var.telegram_bot_token
#   region             = var.region
#   repository_name_telegram   = var.repository_name_telegram
#   job_name_telegram  = var.job_name_telegram
#   }

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

module "generador_ayudantes" {
  source             = "./modules/generador_ayudantes"
  project_id         = var.project_id
  region             = var.region
  repository_name_ayudantes = var.repository_name_ayudantes
  job_name_ayudantes = var.job_name_ayudantes
  topic_name_help = var.topic_name_help
  depends_on = [module.pubsub]
}

module "generador_solicitantes" {
  source             = "./modules/generador_solicitantes"
  project_id         = var.project_id
  region             = var.region
  repository_name_solicitantes = var.repository_name_solicitantes
  job_name_solicitantes = var.job_name_solicitantes
  topic_name_requesters = var.topic_name_requesters
  depends_on = [module.pubsub]
}

module "pubsub" {
  source             = "./modules/pubsub"
  project_id         = var.project_id
  topic_name_help = var.topic_name_help
  subscription_name_help = var.subscription_name_help
}