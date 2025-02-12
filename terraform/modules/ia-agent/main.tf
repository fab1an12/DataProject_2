resource "google_artifact_registry_repository" "agent-api" {
  project  = var.project_id
  location = var.region
  repository_id = var.repository_name_agente
  description   = "Repositorio Docker API de Agente"
  format        = "DOCKER"
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name_agente}/myimage:latest"
}

resource "null_resource" "build_push_image" {
  depends_on = [
    google_artifact_registry_repository.agent-api
  ]

  provisioner "local-exec" {
      command = <<EOT
      gcloud builds submit --region=${var.region} --project=${var.project_id} --tag=${local.image_name} ./modules/ia-agent
  EOT
    }
}

resource "google_cloud_run_service_iam_member" "invoker" {
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_v2_service.agent-api.name
  role     = "roles/run.invoker"
  member   = "allUsers"  
}

resource "google_cloud_run_v2_service" "agent-api" {
  name     = var.job_name_agent
  location = var.region
  deletion_protection = false
  project  = var.project_id
  template {
    containers {
      image = local.image_name

      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      env {
        name  = "LANGCHAIN_TRACING"
        value = var.langchain_tracing
      }
      env {
        name  = "LANGCHAIN_API_KEY"
        value = var.langchain_api_key
      }
      env {
        name  = "TELEGRAM_URL"
        value = ""
      }
    }
  }
  traffic {
    type = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  depends_on = [
    null_resource.build_push_image
  ]
}

