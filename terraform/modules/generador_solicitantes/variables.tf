variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "Región de despliegue de los recursos en Google Cloud"
  type        = string
}


variable "repository_name_solicitantes" {
  description = "Nombre del repositorio de Artifact Registry"
  type        = string
  default = "help-generator"
}

variable "job_name_solicitantes" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "help-generator"
  
}

variable "topic_name_requesters" {
  description = "Nombre del topic de ayudantes"
  type = string
  default = "requesters-topic"
}
