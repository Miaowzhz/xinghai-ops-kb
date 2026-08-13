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
