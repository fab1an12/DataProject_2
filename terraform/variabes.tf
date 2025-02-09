variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

# variable "telegram_bot_token" {
#   description = "Token del bot de Telegram"
#   type        = string
#   sensitive   = true
# }

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
}

variable "repository_name_telegram" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "telegram-api"
}

variable "repository_name_ayudantes" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "help-generator"
}

variable "repository_name_solicitantes" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "help-generator"
}

variable "job_name_telegram" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "telegram-api"
}
variable "job_name_ayudantes" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "help-generator"
}

variable "job_name_solicitantes" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "help-generator"
}

variable "topic_name_help" {
  description = "Nombre del topic de ayudantes"
  type = string
  default = "helpers_topic"
}
variable "topic_name_requesters" {
  description = "Nombre del topic de ayudantes"
  type = string
  default = "requesters-topic"
}

variable "subscription_name_help" {
  description = "Nombre de la suscripción al topic de ayudantes"
  type = string
  default = "helpers_subscription"
}

variable "subscription_name_requesters" {
  description = "Nombre de la suscripción al topic de solicitantes"
  type = string
  default = "requesters_subscription"
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