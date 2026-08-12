import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('xinghai_token') || 'demo-token',
    user: JSON.parse(localStorage.getItem('xinghai_user') || '{"name":"值班工程师","role":"运维团队"}'),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setSession(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('xinghai_token', token)
      localStorage.setItem('xinghai_user', JSON.stringify(user))
    },
    clearSession() {
      this.token = ''
      this.user = null
      localStorage.removeItem('xinghai_token')
      localStorage.removeItem('xinghai_user')
    },
  },
})
