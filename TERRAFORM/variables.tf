variable "project_id" {
  description = "ID del proyecto de GCP"
  type        = string
}

variable "region" {
  description = "Región donde se despliegan los recursos"
  type        = string
  default     = "us-central1"
}

variable "topic_help" {
  description = "Nombre del topic de ayuda en Pub/Sub"
  type        = string
  default     = "topic-help"
}

variable "topic_offer" {
  description = "Nombre del topic de oferta en Pub/Sub"
  type        = string
  default     = "topic-offer"
}
