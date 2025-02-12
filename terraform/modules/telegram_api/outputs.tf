output "telegram_name" {
  description = "Nombre del servicio Telegram"
  value       = google_cloud_run_v2_service.telegram_api.name
}
output "telegram_url" {
  description = "URL del servicio Telegram"
  value       = google_cloud_run_v2_service.telegram_api.uri
}