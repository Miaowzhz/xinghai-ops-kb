import axios from 'axios'
import router from '../router'
import { useAuthStore } from '../stores/auth'

const client = axios.create({ baseURL: '/api', timeout: 15000 })

client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore().clearSession()
      router.push('/login')
    }
    return Promise.reject(error)
  },
)

export default client
