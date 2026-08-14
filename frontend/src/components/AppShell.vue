<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  ChevronsLeft,
  ChevronsRight,
  History,
  LogOut,
  MessageSquare,
  MessageSquareWarning,
  Settings,
  Upload,
} from '@lucide/vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const sidebarCollapsed = ref(localStorage.getItem('xinghai_sidebar_collapsed') === '1')

const primaryItems = [
  { name: '智能问答', icon: MessageSquare, path: '/qa', match: path => path === '/qa' },
  { name: '问答历史记录', icon: History, path: '/qa/history', match: path => path === '/qa/history' },
]

const adminItems = [
  { name: '知识库文档管理', icon: Settings, path: '/documents/manage' },
  { name: '文档上传与入库', icon: Upload, path: '/documents/upload' },
  { name: '反馈审核工作台', icon: MessageSquareWarning, path: '/feedback/audit' },
]

const visibleGroups = computed(() => [
  primaryItems,
  ...(auth.isAdmin ? [adminItems] : []),
])
const roleLabel = computed(() => auth.user?.role === 'admin' ? '管理员' : '运维工程师')

function isActive(item) {
  return item.match ? item.match(route.path) : route.path.startsWith(item.path)
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('xinghai_sidebar_collapsed', sidebarCollapsed.value ? '1' : '0')
}

async function logout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    auth.clearSession()
    router.push('/login')
  } catch {}
}
</script>

<template>
  <div class="app-shell">
    <header class="app-topbar">
      <button class="brand" title="返回智能问答" @click="router.push('/qa')">
        <span class="brand-mark">星</span>
        <span class="brand-copy">
          <strong>星海运维</strong>
          <small>智能知识库</small>
        </span>
      </button>
      <div class="account">
        <span class="account-name">{{ auth.user?.display_name || '用户' }}</span>
        <el-tag type="success" effect="dark">{{ roleLabel }}</el-tag>
        <button class="icon-button" title="退出登录" @click="logout"><LogOut :size="17" /></button>
      </div>
    </header>

    <div class="app-body">
      <aside :class="['app-sidebar', { 'is-collapsed': sidebarCollapsed }]">
        <nav class="global-nav" aria-label="主导航">
          <div v-for="(group, groupIndex) in visibleGroups" :key="groupIndex" :class="['nav-group', { separated: groupIndex > 0 }]">
            <button
              v-for="item in group"
              :key="item.path"
              :class="['global-nav-item', { active: isActive(item) }]"
              :aria-current="isActive(item) ? 'page' : undefined"
              :title="item.name"
              @click="router.push(item.path)"
            >
              <component :is="item.icon" :size="17" />
              <span>{{ item.name }}</span>
            </button>
          </div>
        </nav>
        <div class="sidebar-foot">
          <span class="status-dot"></span>
          <span>知识服务在线</span>
        </div>
        <button
          class="sidebar-toggle"
          :title="sidebarCollapsed ? '展开导航' : '收起导航'"
          :aria-label="sidebarCollapsed ? '展开导航' : '收起导航'"
          @click="toggleSidebar"
        >
          <ChevronsRight v-if="sidebarCollapsed" :size="18" />
          <ChevronsLeft v-else :size="18" />
          <span>{{ sidebarCollapsed ? '展开侧栏' : '收起侧栏' }}</span>
        </button>
      </aside>

      <section class="app-content">
        <slot />
      </section>
    </div>
  </div>
</template>

<style scoped>
.app-shell{height:100vh;display:flex;flex-direction:column;color:#dce8e8;background:#0d171d;overflow:hidden}.app-topbar{height:64px;flex:0 0 64px;display:flex;align-items:center;justify-content:space-between;padding:0 22px 0 18px;border-bottom:1px solid rgba(255,255,255,.07);background:#0a1419;position:relative;z-index:20}.brand{display:flex;align-items:center;gap:10px;border:0;background:transparent;color:inherit;text-align:left;cursor:pointer}.brand-mark{width:34px;height:34px;display:grid;place-items:center;border-radius:8px;background:#178d83;color:#e5fffa;font-family:'Noto Serif SC',serif;font-weight:700}.brand-copy{display:flex;flex-direction:column;gap:1px}.brand-copy strong{font:600 14px 'Noto Serif SC',serif;color:#e4f0ed}.brand-copy small{font-size:10px;color:#61797a}.account{display:flex;align-items:center;gap:10px;color:#a8bcba;font-size:12px}.account :deep(.el-tag){border:0;background:rgba(45,190,143,.13);color:#55d5ae}.icon-button{width:32px;height:32px;display:grid;place-items:center;border:0;border-radius:7px;background:transparent;color:#718787;cursor:pointer}.icon-button:hover{background:rgba(255,255,255,.05);color:#ff9187}.app-body{min-height:0;flex:1;display:flex}.app-sidebar{width:218px;flex:0 0 218px;display:flex;flex-direction:column;padding:12px 12px 14px;border-right:1px solid rgba(255,255,255,.07);background:#0c181d;transition:width .22s ease,flex-basis .22s ease}.app-sidebar.is-collapsed{width:64px;flex-basis:64px;padding-left:8px;padding-right:8px}.sidebar-toggle{width:32px;height:32px;flex:0 0 32px;display:grid;place-items:center;align-self:flex-end;margin:0 4px 10px;border:0;border-radius:6px;background:transparent;color:#688081;cursor:pointer}.sidebar-toggle:hover{background:rgba(255,255,255,.05);color:#5bd2c4}.is-collapsed .sidebar-toggle{align-self:center;margin-left:0;margin-right:0}.global-nav{display:flex;flex-direction:column}.nav-group{display:flex;flex-direction:column;gap:4px}.nav-group.separated{margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,.07)}.global-nav-item{width:100%;height:40px;display:flex;align-items:center;gap:10px;padding:0 11px;border:0;border-radius:7px;background:transparent;color:#809696;font-size:12px;text-align:left;white-space:nowrap;cursor:pointer;transition:background .18s,color .18s}.global-nav-item:hover{background:rgba(255,255,255,.045);color:#d6e5e2}.global-nav-item.active{background:rgba(45,212,191,.1);color:#58d2c3;box-shadow:inset 2px 0 #35b8a8}.is-collapsed .global-nav-item{justify-content:center;padding:0}.is-collapsed .global-nav-item span,.is-collapsed .sidebar-foot span:last-child{display:none}.sidebar-foot{margin-top:auto;display:flex;align-items:center;gap:7px;padding:10px 11px;color:#5e7677;font-size:10px}.is-collapsed .sidebar-foot{justify-content:center;padding:8px}.status-dot{width:6px;height:6px;border-radius:50%;background:#38c89e;box-shadow:0 0 8px rgba(56,200,158,.55)}.app-content{min-width:0;min-height:0;flex:1;overflow:auto;background-image:linear-gradient(rgba(45,212,191,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.018) 1px,transparent 1px);background-size:42px 42px}
@media(max-width:760px){.app-topbar{height:58px;flex-basis:58px;padding:0 12px}.brand-copy small,.account-name,.account :deep(.el-tag){display:none}.app-sidebar,.app-sidebar.is-collapsed{width:64px;flex-basis:64px;padding:8px}.sidebar-toggle{display:none}.global-nav-item{justify-content:center;padding:0}.global-nav-item span,.sidebar-foot span:last-child{display:none}.global-nav-item.active{box-shadow:inset 2px 0 #35b8a8}.sidebar-foot{justify-content:center;padding:8px}.nav-group.separated{margin-top:10px;padding-top:10px}}
</style>

<style scoped>
.sidebar-toggle {
  width: calc(100% + 24px);
  height: 50px;
  flex-basis: 50px;
  align-self: center;
  display: flex;
  justify-content: center;
  gap: 9px;
  margin: 2px -12px -14px;
  border-top: 1px solid rgba(255,255,255,.08);
  border-radius: 0;
  color: #718889;
  font-size: 12px;
}
.sidebar-toggle:hover { background: rgba(255,255,255,.035); }
.is-collapsed .sidebar-toggle {
  width: calc(100% + 16px);
  margin: 2px -8px -14px;
}
.is-collapsed .sidebar-toggle span { display: none; }
@media(max-width:760px) { .sidebar-toggle { display: none; } }
</style>
