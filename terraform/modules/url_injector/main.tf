resource "null_resource" "update-agent" {

  provisioner "local-exec" {
      command = <<EOT
      gcloud run services update ${var.agent_name} --region=${var.region} --project=${var.project_id} --update-env-vars=TELEGRAM_URL=${var.telegram_url}
  EOT
    }
}

resource "null_resource" "update-telegram" {

  provisioner "local-exec" {
      command = <<EOT
      gcloud run services update ${var.telegram_name} --region=${var.region} --project=${var.project_id} --update-env-vars=AGENT_URL=${var.agent_url}
  EOT
    }
}