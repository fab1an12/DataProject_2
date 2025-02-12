module "telegram_api" {
  source             = "./modules/telegram_api"
  project_id         = var.project_id
  telegram_bot_token = var.telegram_bot_token
  region             = var.region
  repository_name_telegram   = var.repository_name_telegram
  job_name_telegram  = var.job_name_telegram
  }

module "ia-agent" {
  source             = "./modules/ia-agent"
  project_id         = var.project_id
  region             = var.region
  openai_api_key     = var.openai_api_key
  langchain_api_key  = var.langchain_api_key
  langchain_tracing = var.langchain_tracing
    repository_name_agente = var.repository_name_agente
  job_name_agent = var.job_name_agent
}
module "injector" {
  source             = "./modules/url_injector"
  project_id         = var.project_id
  region             = var.region
  agent_url    = module.ia-agent.agent_url
  telegram_url       = module.telegram_api.telegram_url
  agent_name   = module.ia-agent.agent_name
  telegram_name      = module.telegram_api.telegram_name
  depends_on         = [module.ia-agent, module.telegram_api]
}
# module "generador_ayudantes" {
#   source             = "./modules/generador_ayudantes"
#   project_id         = var.project_id
#   region             = var.region
#   repository_name_ayudantes = var.repository_name_ayudantes
#   job_name_ayudantes = var.job_name_ayudantes
#   topic_name_help = var.topic_name_help
#   depends_on = [module.pubsub]
# }
# module "generador_solicitantes" {
#   source             = "./modules/generador_solicitantes"
#   project_id         = var.project_id
#   region             = var.region
#   repository_name_solicitantes = var.repository_name_solicitantes
#   job_name_solicitantes =   var.job_name_solicitantes
#   topic_name_tohelp = var.topic_name_tohelp
#   depends_on = [module.pubsub]
# }
# module "pubsub" {
#   source             = "./modules/pubsub"
#   project_id         = var.project_id
#   topic_name_help = var.topic_name_help
#   subscription_name_help = var.subscription_name_help
# }