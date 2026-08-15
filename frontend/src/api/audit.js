import client from './client'

export function getAuditTasks(params) {
  return client.get('/audit/tasks', { params })
}

export function getAuditTaskDetail(taskId) {
  return client.get(`/audit/tasks/${taskId}`)
}

export function resolveAuditTask(taskId, payload) {
  return client.post(`/audit/tasks/${taskId}/resolve`, payload)
}
