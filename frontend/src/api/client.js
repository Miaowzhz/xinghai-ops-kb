import axios from 'axios'
import router from '../router'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：自动添加 Authorization header
client.interceptors.request.use(
  (config) => {
    // 在拦截器内部动态获取 store，避免模块初始化顺序问题
    const token = localStorage.getItem('xinghai_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一处理错误
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    // 401 未登录/登录过期：清空会话并跳转登录页
    if (status === 401) {
      localStorage.removeItem('xinghai_token')
      localStorage.removeItem('xinghai_user')
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }

    // 403 权限不足：可以统一提示
    if (status === 403) {
      console.warn('权限不足:', detail)
    }

    return Promise.reject(error)
  },
)

export default client
