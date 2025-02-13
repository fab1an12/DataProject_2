resource "google_artifact_registry_repository" "help-generator" {
  project  = var.project_id
  location = var.region
  repository_id = var.repository_name_ayudantes
  description   = "Repositorio Docker autogenerador de ayudantes"
  format        = "DOCKER"
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name_ayudantes}/myimage:latest"
}

resource "null_resource" "build_push_image" {
  depends_on = [
    google_artifact_registry_repository.help-generator
  ]

  provisioner "local-exec" {
      command = <<EOT
      gcloud builds submit --region=${var.region} --project=${var.project_id} --tag=${local.image_name} ./modules/generador_ayudantes
  EOT
    }
}

resource "google_cloud_run_v2_job" "help-generator" {
  name     = var.job_name_ayudantes
  location = var.region
  deletion_protection = false
  project = var.project_id
  template {
    template{
      containers {
        image = local.image_name

        env {
          name = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name = "TOPIC_NAME_AYUDANTES"
          value = var.topic_name_help
        }

      }
    }
  }
  depends_on = [
    null_resource.build_push_image
  ]
}
resource "null_resource" "execute_job" {
  depends_on = [
    google_cloud_run_v2_job.help-generator
  ]

  provisioner "local-exec" {
  command = "gcloud run jobs execute ${var.job_name_ayudantes} --region=${var.region} --project=${var.project_id}"
}
}