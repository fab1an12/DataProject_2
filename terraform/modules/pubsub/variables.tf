variable "topic_name_help" {
  description = "Nombre del topic de ayudantes"
  type = string
  default = "helpers_topic"
}
variable "subscription_name_help" {
  description = "Nombre de la suscripción al topic de ayudantes"
  type = string
  default = "helpers_subscription"
  
}
variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}
