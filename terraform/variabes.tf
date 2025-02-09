variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "telegram_bot_token" {
  description = "Token del bot de Telegram"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
}

variable "repository_name" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "telegram-api"
}

variable "job_name" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "telegram-api"
  
}

# variable "openai_api_key" {
#     description = "API Key para OpenAI"
#     type        = string
#     sensitive   = true
# }

# variable "langchain_tracing" {
#     description = "Habilitar trazado para LangChain"
#     type        = string
#     default     = "true"
# }

# variable "langchain_api_key" {
#     description = "API Key para LangChain"
#     type        = string
#     sensitive   = true
# }