variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "environment" {
  description = "Entorno de ejecución"
  type        = string
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
}

variable "cloud_function_runtime" {
  description = "Runtime de la función de Cloud Functions"
  type        = string
  default     = "python310"
}
variable "openai_api_key" {
    description = "API Key para OpenAI"
    type        = string
    sensitive   = true
}

variable "langchain_tracing" {
    description = "Habilitar trazado para LangChain"
    type        = string
    default     = "true"
}

variable "langchain_api_key" {
    description = "API Key para LangChain"
    type        = string
    sensitive   = true
}

