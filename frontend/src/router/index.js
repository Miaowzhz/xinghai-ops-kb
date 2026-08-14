import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DocumentUploadView from '../views/DocumentUploadView.vue'
import DocumentManageView from '../views/DocumentManageView.vue'
import QaView from '../views/QaView.vue'
import QaHistoryView from '../views/QaHistoryView.vue'
import ComingSoonView from '../views/ComingSoonView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/qa' },
    { path: '/workspace', redirect: '/qa' },
    { path: '/login', component: LoginView },
    { path: '/documents/upload', component: DocumentUploadView, meta: { requiresAuth: true, role: 'admin' } },
    { path: '/documents/manage', component: DocumentManageView, meta: { requiresAuth: true, role: 'admin' } },
    { path: '/qa', component: QaView, meta: { requiresAuth: true } },
    { path: '/qa/history', component: QaHistoryView, meta: { requiresAuth: true } },
    { path: '/feedback/audit', component: ComingSoonView, meta: { requiresAuth: true, role: 'admin' } },
    { path: '/:pathMatch(.*)*', redirect: '/qa' },
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

    if (to.meta.role && auth.user?.role !== to.meta.role) {
      return next('/qa')
    }

    return next()
  }

  // 2. 如果已登录用户访问登录页，跳转到工作台
  if (to.path === '/login' && auth.isAuthenticated) {
    return next('/qa')
  }

  next()
})

export default router
