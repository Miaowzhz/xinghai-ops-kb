<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Clock3, MessageSquareMore, Plus, Search } from '@lucide/vue'
import { createSession, getMessages, getSessions } from '../api/qa'

const router = useRouter()
const sessions = ref([])
const messages = ref([])
const keyword = ref('')
const activeSessionId = ref(null)
const loadingSessions = ref(false)
const loadingMessages = ref(false)
const listError = ref(false)
const messageError = ref(false)
const creating = ref(false)
const continuingId = ref(null)
const conversationPanel = ref()

const filteredSessions = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return sessions.value
  return sessions.value.filter(item => item.title.toLowerCase().includes(query))
})
const activeSession = computed(() => sessions.value.find(item => item.id === activeSessionId.value))

const statusMeta = {
  normal: { label: '正常', type: 'success' },
  blocked: { label: '护栏拦截', type: 'danger' },
  refused: { label: '无依据拒答', type: 'warning' },
  failed: { label: '系统失败', type: 'info' },
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replaceAll('/', '-')
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit' })
}

function normalizeMessage(message) {
  return { ...message, citations: Array.isArray(message.citations) ? message.citations : [] }
}

async function loadSessions() {
  loadingSessions.value = true
  listError.value = false
  try {
    sessions.value = await getSessions()
    if (sessions.value.length) await selectSession(sessions.value[0].id, false)
    else { activeSessionId.value = null; messages.value = [] }
  } catch (error) {
    listError.value = true
  } finally {
    loadingSessions.value = false
  }
}

async function selectSession(sessionId, scrollOnMobile = true) {
  if (sessionId === activeSessionId.value && !messageError.value) return
  activeSessionId.value = sessionId
  loadingMessages.value = true
  messageError.value = false
  try {
    messages.value = (await getMessages(sessionId)).map(normalizeMessage)
    await nextTick()
    if (scrollOnMobile && window.innerWidth < 768) conversationPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (error) {
    if (error.response?.status === 404) {
      sessions.value = sessions.value.filter(item => item.id !== sessionId)
      activeSessionId.value = null
      messages.value = []
      ElMessage.error('会话不存在或无权访问')
    } else {
      messageError.value = true
      ElMessage.error('对话记录加载失败')
    }
  } finally {
    loadingMessages.value = false
  }
}

async function startNewQa() {
  creating.value = true
  try {
    const session = await createSession()
    await router.push({ path: '/qa', query: { session_id: session.id } })
  } catch (error) {
    ElMessage.error('创建会话失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

async function continueQa(sessionId) {
  continuingId.value = sessionId
  try {
    await router.push({ path: '/qa', query: { session_id: sessionId } })
  } finally {
    continuingId.value = null
  }
}

onMounted(loadSessions)
</script>

<template>
  <main class="history-page">
    <header class="history-heading">
      <div>
        <span class="heading-kicker">问答档案</span>
        <h1>问答历史记录</h1>
        <p>回看过往会话与引用依据。</p>
      </div>
      <el-button type="primary" :loading="creating" @click="startNewQa"><Plus :size="16" />发起新问答</el-button>
    </header>

    <section class="history-workspace">
      <aside class="archive-pane">
        <div class="archive-tools">
          <el-input v-model="keyword" clearable placeholder="搜索会话标题">
            <template #prefix><Search :size="15" /></template>
          </el-input>
          <span class="session-count">{{ filteredSessions.length }} / {{ sessions.length }}</span>
        </div>

        <div v-loading="loadingSessions" class="archive-list">
          <el-alert v-if="listError" title="会话列表加载失败" type="error" show-icon :closable="false">
            <el-button text type="danger" @click="loadSessions">重新加载</el-button>
          </el-alert>
          <el-empty v-else-if="!sessions.length && !loadingSessions" :image-size="64" description="还没有问答记录" />
          <el-empty v-else-if="!filteredSessions.length" :image-size="56" description="没有匹配的会话" />
          <button
            v-for="session in filteredSessions"
            v-else
            :key="session.id"
            :class="['archive-item', { active: activeSessionId === session.id }]"
            @click="selectSession(session.id)"
          >
            <span class="archive-item-title">{{ session.title }}</span>
            <span class="archive-meta"><MessageSquareMore :size="13" />{{ session.message_count }} 条<Clock3 :size="13" />{{ formatDateTime(session.updated_at) }}</span>
            <span class="continue-link" @click.stop="continueQa(session.id)">
              <span v-if="continuingId !== session.id">继续追问</span>
              <span v-else>正在打开</span>
              <ArrowRight :size="13" />
            </span>
          </button>
        </div>
      </aside>

      <section ref="conversationPanel" v-loading="loadingMessages" class="conversation-pane">
        <template v-if="activeSession">
          <header class="conversation-heading">
            <div>
              <h2>{{ activeSession.title }}</h2>
              <p>共 {{ messages.length }} 条消息 · 最近更新 {{ formatDateTime(activeSession.updated_at) }}</p>
            </div>
            <el-button @click="continueQa(activeSession.id)">继续追问<ArrowRight :size="15" /></el-button>
          </header>

          <div class="conversation-body">
            <el-alert v-if="messageError" title="对话记录加载失败" type="error" show-icon :closable="false">
              <el-button text type="danger" @click="selectSession(activeSession.id)">重试</el-button>
            </el-alert>
            <el-empty v-else-if="!messages.length && !loadingMessages" :image-size="70" description="该会话暂无消息" />
            <article v-for="message in messages" v-else :key="message.id" :class="['history-message', message.role, message.status]">
              <div class="message-avatar">{{ message.role === 'user' ? '我' : '星' }}</div>
              <div class="history-message-content">
                <div class="message-topline">
                  <el-tag v-if="message.role === 'assistant'" :type="(statusMeta[message.status] || statusMeta.normal).type" effect="dark" size="small">
                    {{ (statusMeta[message.status] || statusMeta.normal).label }}
                  </el-tag>
                  <time>{{ formatTime(message.created_at) }}</time>
                </div>
                <div class="history-bubble">{{ message.content }}</div>
                <div v-if="message.role === 'assistant' && message.citations.length" class="history-citations">
                  <div class="citation-heading">引用来源</div>
                  <div v-for="(citation, index) in message.citations" :key="citation.chunk_id || index" class="history-citation">
                    <span class="citation-index">{{ String(index + 1).padStart(2, '0') }}</span>
                    <div>
                      <strong>{{ citation.document_title }}</strong>
                      <div class="citation-meta"><span>{{ citation.product_line }}</span><el-tag size="small" effect="plain">{{ citation.product_version }}</el-tag></div>
                      <p>{{ citation.snippet }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </template>
        <el-empty v-else :image-size="82" description="选择左侧会话查看对话记录" />
      </section>
    </section>
  </main>
</template>

<style scoped>
.history-page{height:100%;min-height:0;display:flex;flex-direction:column;color:#dce8e8;background:#0d171d}.history-heading{flex:0 0 auto;display:flex;align-items:flex-end;justify-content:space-between;padding:30px 36px 24px;border-bottom:1px solid rgba(255,255,255,.07)}.heading-kicker{color:#36b7aa;font:500 10px 'DM Mono',monospace;letter-spacing:1.4px}.history-heading h1{margin:7px 0 0;color:#eff8f5;font:600 27px 'Noto Serif SC',serif}.history-heading p{margin:7px 0 0;color:#708788;font-size:12px}.history-heading :deep(.el-button--primary){border:0;background:#1e9e91}.history-heading :deep(.el-button .lucide){margin-right:6px;vertical-align:-3px}.history-workspace{min-height:0;flex:1;display:grid;grid-template-columns:330px minmax(0,1fr)}.archive-pane{min-height:0;display:flex;flex-direction:column;border-right:1px solid rgba(255,255,255,.07);background:rgba(12,24,29,.68)}.archive-tools{display:flex;align-items:center;gap:10px;padding:18px 16px 14px}.archive-tools :deep(.el-input__wrapper){background:rgba(255,255,255,.035);box-shadow:0 0 0 1px rgba(255,255,255,.09) inset}.archive-tools :deep(.el-input__inner){color:#d7e5e2}.session-count{flex:0 0 auto;color:#60797a;font:10px 'DM Mono',monospace}.archive-list{min-height:0;overflow-y:auto;padding:0 10px 18px}.archive-item{width:100%;position:relative;display:flex;flex-direction:column;align-items:flex-start;gap:8px;padding:15px 13px 36px;border:0;border-left:2px solid transparent;border-bottom:1px solid rgba(255,255,255,.06);background:transparent;color:#9eb2b0;text-align:left;cursor:pointer}.archive-item:hover{background:rgba(255,255,255,.035);color:#d9e8e5}.archive-item.active{border-left-color:#35b8a8;background:rgba(45,212,191,.075);color:#e2f3ef}.archive-item-title{width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;font-weight:500}.archive-meta{display:flex;align-items:center;gap:5px;color:#607879;font-size:10px}.archive-meta svg:nth-of-type(2){margin-left:7px}.continue-link{position:absolute;right:13px;bottom:12px;display:flex;align-items:center;gap:4px;color:#3dbbad;font-size:11px}.conversation-pane{min-width:0;min-height:0;display:flex;flex-direction:column;background:rgba(13,23,29,.72);scroll-margin-top:12px}.conversation-heading{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:13px 28px;border-bottom:1px solid rgba(255,255,255,.07)}.conversation-heading h2{max-width:720px;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#ebf5f2;font:600 18px 'Noto Serif SC',serif}.conversation-heading p{margin:6px 0 0;color:#647c7d;font-size:10px}.conversation-heading :deep(.el-button){border-color:rgba(45,212,191,.24);background:rgba(45,212,191,.055);color:#54ccbe}.conversation-heading :deep(.el-button .lucide){margin-left:5px;vertical-align:-3px}.conversation-body{min-height:0;flex:1;overflow-y:auto;padding:26px max(28px,calc((100% - 900px)/2)) 36px}.history-message{display:flex;align-items:flex-start;gap:10px;max-width:900px;margin:0 auto 24px}.history-message.user{flex-direction:row-reverse}.message-avatar{width:29px;height:29px;flex:0 0 29px;display:grid;place-items:center;border:1px solid rgba(45,212,191,.22);border-radius:7px;background:rgba(45,212,191,.11);color:#59d3c4;font-size:11px}.history-message.user .message-avatar{border-color:rgba(74,144,226,.25);background:rgba(74,144,226,.12);color:#91c2ff}.history-message-content{max-width:80%}.message-topline{height:23px;display:flex;align-items:flex-start;gap:8px;color:#5e7576;font-size:10px}.history-message.user .message-topline{justify-content:flex-end}.message-topline :deep(.el-tag){height:19px;border:0;font-size:9px}.message-topline :deep(.el-tag--success){background:rgba(45,190,143,.13);color:#55d5ae}.message-topline :deep(.el-tag--danger){background:rgba(245,104,94,.13);color:#ff9187}.message-topline :deep(.el-tag--warning){background:rgba(237,160,70,.13);color:#f5be73}.message-topline :deep(.el-tag--info){background:rgba(145,166,167,.12);color:#9aacac}.history-bubble{white-space:pre-wrap;color:#d5e4e1;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:4px 10px 10px 10px;padding:14px 16px;font-size:13px;line-height:1.75}.history-message.user .history-bubble{border:0;border-radius:10px 4px 10px 10px;background:#176e6a;color:#effefa}.history-message.blocked .history-bubble{border-color:rgba(245,104,94,.2);background:rgba(245,104,94,.08);color:#ffaaa3}.history-message.refused .history-bubble{border-color:rgba(237,160,70,.2);background:rgba(237,160,70,.08);color:#f4c789}.history-message.failed .history-bubble{border-color:rgba(145,166,167,.17);background:rgba(145,166,167,.07);color:#aababa}.history-citations{margin-top:9px;padding:12px;border:1px solid rgba(45,212,191,.12);border-radius:7px;background:rgba(45,212,191,.035)}.citation-heading{margin-bottom:8px;color:#6b9994;font-size:10px}.history-citation{display:grid;grid-template-columns:24px 1fr;gap:8px;padding:9px 0;border-top:1px solid rgba(255,255,255,.055)}.history-citation:first-of-type{border-top:0}.citation-index{color:#3fc0b2;font:10px 'DM Mono',monospace}.history-citation strong{color:#cbdedb;font-size:11px}.citation-meta{display:flex;align-items:center;gap:7px;margin-top:4px;color:#60958f;font-size:9px}.citation-meta :deep(.el-tag){height:17px;border-color:rgba(45,212,191,.2);color:#69b8af;background:transparent;font-size:9px}.history-citation p{margin:6px 0 0;color:#7d9493;font-size:10px;line-height:1.55}.conversation-pane>.el-empty{margin:auto}.history-page :deep(.el-empty__description p){color:#6d8384}.history-page :deep(.el-alert){background:rgba(185,59,60,.1)}
@media(max-width:900px){.history-workspace{grid-template-columns:285px minmax(0,1fr)}.conversation-body{padding-left:20px;padding-right:20px}.history-heading{padding-left:26px;padding-right:26px}}
@media(max-width:767px){.history-page{height:auto;min-height:100%}.history-heading{align-items:flex-start;gap:16px;padding:22px 16px 18px}.history-heading h1{font-size:23px}.history-heading p{display:none}.history-heading :deep(.el-button span){font-size:0}.history-heading :deep(.el-button .lucide){margin:0}.history-workspace{display:flex;flex-direction:column}.archive-pane{height:250px;flex:0 0 250px;border-right:0;border-bottom:1px solid rgba(255,255,255,.07)}.archive-tools{padding:12px}.archive-list{padding:0 8px 10px}.archive-item{padding-top:11px;padding-bottom:31px}.conversation-pane{min-height:560px}.conversation-heading{align-items:flex-start;padding:15px 16px}.conversation-heading h2{font-size:16px}.conversation-heading :deep(.el-button span){font-size:0}.conversation-heading :deep(.el-button .lucide){margin:0}.conversation-body{padding:20px 12px 30px}.history-message-content{max-width:86%}}
</style>
