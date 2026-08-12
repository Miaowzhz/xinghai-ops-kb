import { defineStore } from 'pinia'
import { login as apiLogin, getProfile } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('xinghai_token') || '',
    user: JSON.parse(localStorage.getItem('xinghai_user') || 'null'),
    profileLoaded: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    /**
     * 设置登录会话（token + 用户信息），同时写入 localStorage
     */
    setSession(token, user) {
      this.token = token
      this.user = user
      this.profileLoaded = true
      localStorage.setItem('xinghai_token', token)
      localStorage.setItem('xinghai_user', JSON.stringify(user))
    },

    /**
     * 清空会话，同时清除 localStorage
     */
    clearSession() {
      this.token = ''
      this.user = null
      this.profileLoaded = false
      localStorage.removeItem('xinghai_token')
      localStorage.removeItem('xinghai_user')
    },

    /**
     * 调用登录接口
     */
    async login(username, password) {
      const data = await apiLogin(username, password)
      this.setSession(data.access_token, data.user)
      return data
    },

    /**
     * 拉取最新的用户信息（路由守卫进入页面前调用）
     */
    async fetchProfile() {
      if (!this.token) {
        this.clearSession()
        throw new Error('No token')
      }
      try {
        const user = await getProfile()
        this.user = user
        this.profileLoaded = true
        localStorage.setItem('xinghai_user', JSON.stringify(user))
        return user
      } catch (error) {
        // 如果 401，拦截器已经处理了清除 token
        this.profileLoaded = false
        throw error
      }
    },
  },
})
