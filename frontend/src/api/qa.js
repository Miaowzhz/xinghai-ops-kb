import client from './client'

export function getSessions() {
  return client.get('/qa/sessions')
}

export function createSession(title) {
  return client.post('/qa/sessions', title ? { title } : {})
}

export function getMessages(sessionId) {
  return client.get(`/qa/sessions/${sessionId}/messages`)
}

export async function streamChat(payload, onEvent) {
  const token = localStorage.getItem('xinghai_token')
  const response = await fetch('/api/qa/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  if (!response.body) throw new Error('响应不支持流式读取')

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    for (const event of events) {
      const dataLine = event.split('\n').find(line => line.startsWith('data: '))
      if (!dataLine) continue
      try { onEvent(JSON.parse(dataLine.slice(6))) } catch (error) { console.warn('忽略无法解析的 SSE 事件', error) }
    }
    if (done) break
  }
}
