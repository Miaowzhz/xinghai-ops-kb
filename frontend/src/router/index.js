import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import WorkspaceView from '../views/WorkspaceView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/workspace' },
    {
      path: '/workspace',
      component: WorkspaceView,
      meta: { requiresAuth: true },
    },
    { path: '/login', component: LoginView },
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // 1. 如果访问需要认证的页面
  if (to.meta.requiresAuth) {
    // 没有 token，直接跳登录
    if (!auth.isAuthenticated) {
      return next('/login')
    }

    // 有 token 但还没拉取过用户信息（页面刷新场景），先拉取 profile
    if (!auth.profileLoaded) {
      try {
        await auth.fetchProfile()
      } catch (error) {
        // 拉取失败（token 过期/无效），已经被拦截器清理，跳登录
        return next('/login')
      }
    }

    return next()
  }

  // 2. 如果已登录用户访问登录页，跳转到工作台
  if (to.path === '/login' && auth.isAuthenticated) {
    return next('/workspace')
  }

  next()
})

export default router
