output "agent_url" {
  description = "URL del servicio agent"
  value       = google_cloud_run_v2_service.agent-api.uri
}
output "agent_name" {
  description = "Nombre del servicio agent"
  value       = google_cloud_run_v2_service.agent-api.name
}