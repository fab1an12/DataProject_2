variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
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

variable "repository_name_agente" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "agent-api"
}

variable "job_name_agent" {
  description = "Nombre del trabajo de Cloud Run"
  type        = string
  default     = "agent-api"
}