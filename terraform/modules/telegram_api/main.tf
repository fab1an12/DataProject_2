resource "google_storage_bucket" "telegram_api_bucket" {
  name          = "${var.project_id}-telegram-api"
  location      = var.region
  force_destroy = true
}

resource "google_storage_bucket_object" "telegram_api_bucket_object" {
  name   = "telegram-api"
  bucket = google_storage_bucket.telegram_api_bucket.name
  source = "${path.module}/telegram_api.zip"
}

resource "google_cloudfunctions2_function" "telegram_api" {
  name        = "telegram-api"
  location    = var.region
  project = var.project_id
  description = "API para leer y escribir en Telegram"

  build_config {
    runtime     = var.cloud_function_runtime
    entry_point = "app"
    source {
      storage_source {
        bucket = google_storage_bucket.telegram_api_bucket.name
        object = google_storage_bucket_object.telegram_api_bucket_object.name
      }
    }
  }

  service_config {
    min_instance_count = 0
    max_instance_count = 5
    available_memory = "256M"
    timeout_seconds = 60
    environment_variables = {
      TELEGRAM_BOT_TOKEN = var.telegram_bot_token
      ENVIRONMENT    = var.environment
    }
  }
}

resource "google_cloudfunctions2_function_iam_member" "allow_all" {
  cloud_function = google_cloudfunctions2_function.telegram_api.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

resource "null_resource" "set_telegram_webhook" {
  provisioner "local-exec" {
    command = <<EOT
      curl -X POST "https://api.telegram.org/bot${var.telegram_bot_token}/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://${google_cloudfunctions2_function.telegram_api.url}/webhook"}'
    EOT
  }
  depends_on = [google_cloudfunctions2_function.telegram_api]
}