# Crear un topic en Pub/Sub para las solicitudes de ayuda
resource "google_pubsub_topic" "help" {
  name = var.topic_help
}

# Crear un topic en Pub/Sub para las ofertas de ayuda
resource "google_pubsub_topic" "offer" {
  name = var.topic_offer
}

# Crear una suscripción para escuchar mensajes del topic de ayuda
resource "google_pubsub_subscription" "help_subscription" {
  name  = "${var.topic_help}-subscription"
  topic = google_pubsub_topic.help.name
}

# Crear una suscripción para escuchar mensajes del topic de ofertas
resource "google_pubsub_subscription" "offer_subscription" {
  name  = "${var.topic_offer}-subscription"
  topic = google_pubsub_topic.offer.name
}
