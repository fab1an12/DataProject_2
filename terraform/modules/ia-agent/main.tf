resource "google_storage_bucket" "agent_api_bucket" {
  name          = "${var.project_id}-agent-api"
  project = var.project_id
  location      = var.region
  force_destroy = true
}

resource "google_storage_bucket_object" "agent_api_bucket_object" {
  name   = "agent-api"
  bucket = google_storage_bucket.agent_api_bucket.name
  source = "${path.module}/agent.zip"
}

resource "google_cloudfunctions2_function" "agent_api" {
  name     = "agent-api"
  project  = var.project_id
  location = var.region
  description = "API para el agente de IA"

  build_config {
    runtime     = var.cloud_function_runtime
    entry_point = "app"

    source {
      storage_source {
        bucket = google_storage_bucket.agent_api_bucket.name
        object = google_storage_bucket_object.agent_api_bucket_object.name
      }
    }
  }

  service_config {
    environment_variables = {
      OPENAI_API_KEY     = var.openai_api_key
      LANGCHAIN_API_KEY  = var.langchain_api_key
      LANGCHAIN_TRACING  = var.langchain_tracing
      ENVIRONMENT    = var.environment
    }
    min_instance_count = 0
    max_instance_count = 5
    available_memory = "256M"
    timeout_seconds = 60
  }

  depends_on = [
    google_storage_bucket_object.agent_api_bucket_object
  ]
}

resource "google_cloudfunctions2_function_iam_member" "allow_all" {
  cloud_function = google_cloudfunctions2_function.agent_api.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}