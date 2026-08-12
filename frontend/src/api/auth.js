import client from './client'

/**
 * 登录接口
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<{access_token: string, token_type: string, user: {id: number, username: string, display_name: string, role: string}}>}
 */
export function login(username, password) {
  return client.post('/auth/login', { username, password })
}

/**
 * 获取当前登录用户信息
 * @returns {Promise<{id: number, username: string, display_name: string, role: string}>}
 */
export function getProfile() {
  return client.get('/auth/profile')
}
