resource "google_artifact_registry_repository" "telegram-api" {
  project  = var.project_id
  location = var.region
  repository_id = var.repository_name_telegram
  description   = "Repositorio Docker API de Telegram"
  format        = "DOCKER"
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name_telegram}/myimage:latest"
}

resource "null_resource" "build_push_image" {
  depends_on = [
    google_artifact_registry_repository.telegram-api
  ]

  provisioner "local-exec" {
      command = <<EOT
      gcloud builds submit --region=${var.region} --project=${var.project_id} --tag=${local.image_name} ./modules/telegram_api
  EOT
    }
}

resource "google_cloud_run_service_iam_member" "invoker" {
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_v2_service.telegram_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"  
}

resource "google_cloud_run_v2_service" "telegram_api" {
  name     = var.job_name_telegram
  location = var.region
  deletion_protection = false
  project  = var.project_id
  template {
    containers {
      image = local.image_name

      env {
        name  = "TELEGRAM_BOT_TOKEN"
        value = var.telegram_bot_token
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