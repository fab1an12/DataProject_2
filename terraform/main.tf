module "telegram_api" {
  source             = "./modules/telegram_api"
  project_id         = var.project_id
  telegram_bot_token = var.telegram_bot_token
  environment        = var.environment
  region             = var.region
  cloud_function_runtime = var.cloud_function_runtime
}