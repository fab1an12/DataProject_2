resource "google_artifact_registry_repository" "tohelp-generator" {
  project  = var.project_id
  location = var.region
  repository_id = var.repository_name_solicitantes
  description   = "Repositorio Docker autogenerador de solicitantes"
  format        = "DOCKER"
}

locals {
  image_name = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name_solicitantes}/myimage:latest"
}

resource "null_resource" "build_push_image" {
  depends_on = [
    google_artifact_registry_repository.tohelp-generator
  ]

  provisioner "local-exec" {
      command = <<EOT
      gcloud builds submit --region=${var.region} --project=${var.project_id} --tag=${local.image_name} ./modules/generador_solicitantes
  EOT
    }
}

resource "google_cloud_run_v2_job" "tohelp-generator" {
  name     = var.job_name_solicitantes
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
          name = "TOPIC_NAME_SOLICITANTES"
          value = var.topic_name_tohelp
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
    google_cloud_run_v2_job.tohelp-generator
  ]

  provisioner "local-exec" {
    command = <<EOT
gcloud run jobs execute ${google_cloud_run_v2_job.tohelp-generator.name} \
  --region=${var.region} \
  --project=${var.project_id}
EOT
  }
}