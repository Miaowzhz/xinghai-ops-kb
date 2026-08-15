import client from './client'

export function getGuardrailRules() {
  return client.get('/guardrail/rules')
}

export function createGuardrailRule(payload) {
  return client.post('/guardrail/rules', payload)
}

export function updateGuardrailRule(ruleId, payload) {
  return client.put(`/guardrail/rules/${ruleId}`, payload)
}
