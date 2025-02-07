variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "telegram_bot_token" {
  description = "Token del bot de Telegram"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Entorno de ejecución"
  type        = string
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
  default     = "europe-southwest1"
}

variable "cloud_function_runtime" {
  description = "Runtime de la función de Cloud Functions"
  type        = string
  default     = "python310"
}