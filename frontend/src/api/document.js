import client from './client'

export function uploadDocument(formData) {
  return client.post('/documents/upload', formData)
}

export function getDocumentList(params) {
  return client.get('/documents', { params })
}

export function getDocumentDetail(docId) {
  return client.get(`/documents/${docId}`)
}

export function reingestDocument(docId, formData) {
  return client.post(`/documents/${docId}/reingest`, formData)
}

export function deleteDocument(docId) {
  return client.delete(`/documents/${docId}`)
}
