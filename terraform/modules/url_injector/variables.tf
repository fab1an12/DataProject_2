variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
}
variable "agent_url" {
  type        = string
  description = "URL que se inyectará en la variable de entorno AGENT_URL"
}

variable "telegram_url" {
  type        = string
  description = "URL que se inyectará en la variable de entorno TELEGRAM_URL"
}

variable "agent_name" {
  type        = string
  description = "Nombre del servicio Cloud Run (Agente) a actualizar"
}

variable "telegram_name" {
  type        = string
  description = "Nombre del servicio Cloud Run (Telegram) a actualizar"
}