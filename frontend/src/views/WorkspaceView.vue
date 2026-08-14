<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Send, LogOut, MessageSquare, History,
  Settings, Upload, MessageSquareWarning,
  Sparkles
} from '@lucide/vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const question = ref('')
const activeNav = ref('智能问答')
const isAsking = ref(false)

// 基础导航项
const baseNavItems = [
  { name: '智能问答', icon: MessageSquare },
  { name: '问答历史记录', icon: History },
]

// 管理员专属导航项
const adminNavItems = [
  { name: '知识库文档管理', icon: Settings },
  { name: '文档上传与入库', icon: Upload },
  { name: '反馈审核工作台', icon: MessageSquareWarning },
]

const allNavItems = computed(() => {
  const items = [...baseNavItems]
  if (auth.isAdmin) {
    items.push(...adminNavItems)
  }
  return items
})

// 获取头像首字
const avatarChar = computed(() => auth.user?.display_name?.charAt(0) || '用')
const roleLabel = computed(() => auth.user?.role === 'admin' ? '管理员' : '工程师')

// 快捷问题
const quickQuestions = [
  '如何排查 Pod CrashLoopBackOff？',
  'MySQL 主从延迟怎么处理？',
  'Nginx 502 Bad Gateway 排查思路',
  'Redis 内存满了怎么办？',
]

// 模拟提问（后续对接真实接口）
function submitQuestion() {
  if (!question.value.trim()) {
    ElMessage.info('请输入你的问题')
    return
  }
  isAsking.value = true
  setTimeout(() => {
    isAsking.value = false
    ElMessage.info('AI 问答接口接入中，敬请期待')
    question.value = ''
  }, 1000)
}

function handleQuickQ(q) {
  question.value = q
}

function handleNavClick(item) {
  activeNav.value = item.name
  if (item.name === '智能问答') {
    router.push('/qa')
    return
  }
  if (item.name === '文档上传与入库') {
    router.push('/documents/upload')
    return
  }
  if (item.name === '知识库文档管理') {
    router.push('/documents/manage')
    return
  }
  if (adminNavItems.some(n => n.name === item.name)) {
    ElMessage.info(`「${item.name}」功能开发中`)
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
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
  <div class="workspace">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-small">
          <span>星</span>
        </div>
        <span class="logo-text">星海</span>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in allNavItems"
          :key="item.name"
          :class="['nav-item', { active: activeNav === item.name, admin: adminNavItems.some(n => n.name === item.name) }]"
          @click="handleNavClick(item)"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.name }}</span>
          <span v-if="adminNavItems.some(n => n.name === item.name)" class="admin-dot"></span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="user-card" @click="handleLogout">
          <div class="avatar-small">{{ avatarChar }}</div>
          <div class="user-info-small">
            <span class="user-name">{{ auth.user?.display_name }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
          <LogOut :size="16" class="logout-icon" />
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-area">
      <!-- 顶部欢迎 -->
      <div class="welcome-section">
        <div class="welcome-text">
          <h1>你好，{{ auth.user?.display_name }} 👋</h1>
          <p>有什么运维问题，随时问我</p>
        </div>
      </div>

      <!-- 问答区域 -->
      <div class="qa-section">
        <div class="ask-box">
          <div class="ask-icon">
            <Sparkles :size="22" />
          </div>
          <div class="ask-input-wrap">
            <textarea
              v-model="question"
              placeholder="输入你的运维问题，我会从知识库中为你找到答案..."
              rows="1"
              @keydown.enter.exact.prevent="submitQuestion"
            ></textarea>
          </div>
          <button
            class="ask-btn"
            :class="{ ready: question.trim(), loading: isAsking }"
            :disabled="isAsking"
            @click="submitQuestion"
          >
            <Send v-if="!isAsking" :size="18" />
            <span v-else class="loading-dots">
              <i></i><i></i><i></i>
            </span>
          </button>
        </div>

        <!-- 快捷提问 -->
        <div class="quick-questions">
          <span class="quick-label">常见问题：</span>
          <button
            v-for="q in quickQuestions"
            :key="q"
            class="quick-tag"
            @click="handleQuickQ(q)"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <!-- 空状态提示（后续有对话时替换为消息列表） -->
      <div class="empty-hint">
        <div class="hint-icon">
          <Search :size="32" />
        </div>
        <p>输入问题开始搜索知识库</p>
        <small>支持自然语言提问，AI 会帮你定位最相关的文档</small>
      </div>
    </main>

    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
    </div>
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  min-height: 100vh;
  background: #0f1923;
  color: #e2e8f0;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.15;
}

.bg-orb-1 {
  width: 500px;
  height: 500px;
  background: #2dd4bf;
  top: -200px;
  right: -100px;
}

.bg-orb-2 {
  width: 400px;
  height: 400px;
  background: #3b82f6;
  bottom: -150px;
  left: 100px;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  height: 100vh;
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  position: relative;
  z-index: 10;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 40px;
  padding: 0 8px;
}

.logo-small {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 700;
  color: white;
}

.logo-text {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: rgba(148, 163, 184, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  width: 100%;
  text-align: left;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

.nav-item.active {
  background: rgba(45, 212, 191, 0.1);
  color: #2dd4bf;
}

.nav-item.admin {
  margin-top: 20px;
}

.nav-item.admin::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 14px;
  right: 14px;
  height: 1px;
  background: rgba(255, 255, 255, 0.05);
}

.admin-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f59e0b;
  margin-left: auto;
}

/* 用户卡片 */
.sidebar-footer {
  margin-top: auto;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-card:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-card:hover .logout-icon {
  opacity: 1;
}

.avatar-small {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(45, 212, 191, 0.2), rgba(59, 130, 246, 0.2));
  border: 1px solid rgba(45, 212, 191, 0.3);
  display: grid;
  place-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #2dd4bf;
  flex-shrink: 0;
}

.user-info-small {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.6);
}

.logout-icon {
  color: rgba(148, 163, 184, 0.4);
  opacity: 0;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

/* 主内容区 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 48px 12%;
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.welcome-section {
  margin-bottom: 48px;
  animation: fadeInDown 0.6s ease both;
}

.welcome-text h1 {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 8px;
  background: linear-gradient(135deg, #f1f5f9, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-text p {
  margin: 0;
  color: rgba(148, 163, 184, 0.7);
  font-size: 15px;
}

/* 问答区域 */
.qa-section {
  animation: fadeInUp 0.6s ease 0.1s both;
}

.ask-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px 20px;
  transition: all 0.3s ease;
}

.ask-box:focus-within {
  border-color: rgba(45, 212, 191, 0.4);
  box-shadow: 0 0 30px rgba(45, 212, 191, 0.1);
}

.ask-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(45, 212, 191, 0.15), rgba(59, 130, 246, 0.15));
  display: grid;
  place-items: center;
  color: #2dd4bf;
  flex-shrink: 0;
  margin-top: 2px;
}

.ask-input-wrap {
  flex: 1;
}

.ask-input-wrap textarea {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  min-height: 24px;
  max-height: 200px;
  font-family: inherit;
}

.ask-input-wrap textarea::placeholder {
  color: rgba(148, 163, 184, 0.4);
}

.ask-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: rgba(148, 163, 184, 0.1);
  color: rgba(148, 163, 184, 0.3);
  display: grid;
  place-items: center;
  cursor: not-allowed;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-top: 2px;
}

.ask-btn.ready {
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(45, 212, 191, 0.3);
}

.ask-btn.ready:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(45, 212, 191, 0.4);
}

.ask-btn.loading {
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  cursor: wait;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.loading-dots i:nth-child(2) { animation-delay: 0.2s; }
.loading-dots i:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 快捷问题 */
.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  align-items: center;
}

.quick-label {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.5);
  margin-right: 4px;
}

.quick-tag {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-tag:hover {
  background: rgba(45, 212, 191, 0.1);
  border-color: rgba(45, 212, 191, 0.3);
  color: #2dd4bf;
}

/* 空状态 */
.empty-hint {
  margin-top: auto;
  padding-top: 80px;
  text-align: center;
  animation: fadeIn 0.8s ease 0.3s both;
}

.hint-icon {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.02);
  display: grid;
  place-items: center;
  margin: 0 auto 20px;
  color: rgba(148, 163, 184, 0.2);
}

.empty-hint p {
  margin: 0 0 6px;
  font-size: 15px;
  color: rgba(148, 163, 184, 0.5);
}

.empty-hint small {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.3);
}

/* 动画 */
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
