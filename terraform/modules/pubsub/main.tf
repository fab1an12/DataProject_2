resource "google_pubsub_topic" "help_topic" {
    project = var.project_id
    name = var.topic_name_help
}

resource "google_pubsub_subscription" "help_subscription" {
  name  = var.subscription_name_help
  project = var.project_id
  topic = google_pubsub_topic.help_topic.id
  ack_deadline_seconds = 20
}