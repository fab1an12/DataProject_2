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
  default = "tohelp-generator"
}

variable "job_name_solicitantes" {
  description = "Nombre del job de Cloud Build"
  type        = string
  default     = "tohelp-generator"
  
}

variable "topic_name_tohelp" {
  description = "Nombre del topic de solicitantes"
  type = string
  default = "tohelp_topic"
}
