import client from './client'

export function submitFeedback(payload) {
  return client.post('/feedback', payload)
}
