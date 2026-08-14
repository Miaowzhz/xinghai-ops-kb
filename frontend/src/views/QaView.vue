<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { History, MessageSquarePlus, Send, ThumbsDown, ThumbsUp } from '@lucide/vue'
import { createSession, getMessages, getSessions, streamChat } from '../api/qa'
import { submitFeedback } from '../api/feedback'

const route = useRoute()
const sessions = ref([])
const messages = ref([])
const activeSessionId = ref(null)
const question = ref('')
const productLine = ref('')
const loadingSessions = ref(false)
const loadingMessages = ref(false)
const streaming = ref(false)
const listError = ref(false)
const messageError = ref(false)
const feedbackDialog = ref(false)
const feedbackMessage = ref(null)
const feedbackReason = ref('')
const feedbackSubmitting = ref(false)
const scrollBox = ref()
const feedbackForm = ref()

const productLines = ['ECS', 'VPC', 'RDS']
const feedbackRules = { reason: [{ required: true, message: '请填写点踩原因，方便管理员定位问题', trigger: 'blur' }, { min: 1, max: 500, message: '原因长度为 1-500 个字符', trigger: 'blur' }] }
const activeSession = computed(() => sessions.value.find(item => item.id === activeSessionId.value))
const historyMode = computed(() => route.path === '/qa/history')

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
function formatFullTime(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '' }
function scrollToBottom() { nextTick(() => { if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight }) }
function normalizeMessage(message) { return { ...message, citations: Array.isArray(message.citations) ? message.citations : [] } }

async function loadSessions(selectFirst = true) {
  loadingSessions.value = true; listError.value = false
  try {
    sessions.value = await getSessions()
    if (selectFirst && sessions.value.length) await selectSession(sessions.value[0].id)
  } catch (error) { listError.value = true; ElMessage.error('会话列表加载失败') } finally { loadingSessions.value = false }
}
async function selectSession(sessionId) {
  if (streaming.value || sessionId === activeSessionId.value && messages.value.length) return
  activeSessionId.value = sessionId; loadingMessages.value = true; messageError.value = false
  try { messages.value = (await getMessages(sessionId)).map(normalizeMessage); scrollToBottom() } catch (error) { messageError.value = true; ElMessage.error('消息加载失败') } finally { loadingMessages.value = false }
}
async function newSession() {
  if (streaming.value) return
  try {
    const session = await createSession()
    sessions.value.unshift(session); activeSessionId.value = session.id; messages.value = []; question.value = ''
  } catch (error) { ElMessage.error('创建会话失败，请重试') }
}
function handleEnter(event) { if (!event.shiftKey) { event.preventDefault(); sendQuestion() } }
async function sendQuestion() {
  const content = question.value.trim()
  if (!content || streaming.value) return
  if (!activeSessionId.value) {
    try { const session = await createSession(content.slice(0, 50)); sessions.value.unshift(session); activeSessionId.value = session.id } catch { ElMessage.error('创建会话失败，请重试'); return }
  }
  const userMessage = { id: `local-user-${Date.now()}`, role: 'user', content, status: 'normal', created_at: new Date().toISOString() }
  const assistantMessage = { id: `local-assistant-${Date.now()}`, role: 'assistant', content: '', citations: [], status: 'normal', created_at: new Date().toISOString(), streaming: true }
  messages.value.push(userMessage, assistantMessage); question.value = ''; streaming.value = true; scrollToBottom()
  try {
    await streamChat({ session_id: activeSessionId.value, question: content, ...(productLine.value ? { product_line: productLine.value } : {}) }, event => {
      if (event.type === 'token') assistantMessage.content += event.content || ''
      if (event.type === 'citations') assistantMessage.citations = event.items || []
      if (event.type === 'status') assistantMessage.status = event.status
      if (event.type === 'error') { assistantMessage.status = 'failed'; assistantMessage.content = event.message || '系统繁忙，请稍后重试。'; ElMessage.error(assistantMessage.content) }
      if (event.type === 'done') { activeSessionId.value = event.session_id; assistantMessage.streaming = false }
      scrollToBottom()
    })
    assistantMessage.streaming = false
    await loadSessions(false)
  } catch (error) { assistantMessage.status = 'failed'; assistantMessage.streaming = false; assistantMessage.content = '网络异常，回答中断，请重试'; ElMessage.error(assistantMessage.content) } finally { streaming.value = false }
}
function openDislike(message) { feedbackMessage.value = message; feedbackReason.value = ''; feedbackForm.value?.clearValidate(); feedbackDialog.value = true }
async function likeMessage(message) { await sendFeedback(message, 'like', null) }
async function submitDislike() {
  await feedbackForm.value.validate(async valid => { if (valid) await sendFeedback(feedbackMessage.value, 'dislike', feedbackReason.value.trim()) })
}
async function sendFeedback(message, type, reason) {
  if (String(message.id).startsWith('local-')) { ElMessage.info('回答完成后才能提交反馈'); return }
  feedbackSubmitting.value = true
  try { await submitFeedback({ message_id: message.id, feedback_type: type, reason }); message.feedback_type = type; feedbackDialog.value = false; ElMessage.success(type === 'like' ? '感谢反馈' : '已记录，将转交知识管理员审核') } catch (error) { ElMessage.error('反馈提交失败，请重试') } finally { feedbackSubmitting.value = false }
}
onMounted(() => loadSessions())
</script>

<template>
  <div class="qa-page">
    <div class="qa-shell">
      <aside class="session-sidebar">
        <button class="new-session" :disabled="streaming" @click="newSession"><MessageSquarePlus :size="17" />新建会话</button>
        <div class="session-label"><History :size="14" />会话历史</div>
        <div v-if="loadingSessions" class="session-loading">正在加载会话...</div>
        <div v-else-if="listError" class="session-error"><p>会话列表加载失败</p><el-button text @click="loadSessions">重试</el-button></div>
        <div v-else class="session-list"><button v-for="session in sessions" :key="session.id" :class="['session-item', { active: activeSessionId === session.id }]" :disabled="streaming" @click="selectSession(session.id)"><span class="session-title">{{ session.title }}</span><small>{{ formatTime(session.updated_at) }}</small></button></div>
      </aside>
      <main class="chat-main">
        <div class="chat-heading"><div><span class="chat-kicker">{{ historyMode ? '问答历史记录' : '运维知识问答' }}</span><h1>{{ activeSession?.title || (historyMode ? '选择一条历史会话' : '从问题开始') }}</h1></div><span class="chat-state" :class="{ active: streaming }">{{ streaming ? '正在生成回答' : '知识库已就绪' }}</span></div>
        <div ref="scrollBox" class="messages-area">
          <el-empty v-if="!loadingMessages && !messages.length" :image-size="80" description="暂无会话，输入问题开始你的第一次提问" />
          <div v-if="loadingMessages" class="message-loading">正在加载消息...</div>
          <el-alert v-if="messageError" title="消息加载失败" type="error" show-icon :closable="false"><el-button text type="danger" @click="selectSession(activeSessionId)">重试</el-button></el-alert>
          <article v-for="message in messages" :key="message.id" :class="['message-row', message.role, message.status]">
            <div class="message-avatar">{{ message.role === 'user' ? '我' : '星' }}</div>
            <div class="message-content"><div v-if="message.status === 'blocked'" class="blocked-message"><strong>安全提醒</strong><p>{{ message.content }}</p></div><div v-else-if="message.status === 'failed'" class="failed-message">{{ message.content }}</div><div v-else class="message-bubble">{{ message.content }}<span v-if="message.streaming" class="typing-cursor"></span><div v-if="message.role === 'assistant' && message.citations?.length" class="citations"><div class="citations-title">引用来源</div><div v-for="(citation, index) in message.citations" :key="citation.chunk_id || index" class="citation-card"><span class="citation-index">[{{ index + 1 }}]</span><div><strong>{{ citation.document_title }}</strong><small>{{ citation.product_line }} · {{ citation.product_version }}</small><p>{{ citation.snippet }}</p></div></div></div><div v-if="message.role === 'assistant' && ['normal', 'refused'].includes(message.status) && !message.streaming" class="feedback-row"><button :class="{ selected: message.feedback_type === 'like' }" title="有帮助" @click="likeMessage(message)"><ThumbsUp :size="14" /></button><button :class="{ selected: message.feedback_type === 'dislike' }" title="没有帮助" @click="openDislike(message)"><ThumbsDown :size="14" /></button><span>{{ formatFullTime(message.created_at) }}</span></div></div><small v-if="message.role === 'user'" class="message-time">{{ formatFullTime(message.created_at) }}</small></div>
          </article>
        </div>
        <div class="composer"><div class="composer-tools"><span>检索范围</span><el-select v-model="productLine" placeholder="全部产品线" clearable :disabled="streaming"><el-option label="全部产品线" value="" /><el-option v-for="line in productLines" :key="line" :label="line" :value="line" /></el-select><small>Enter 发送 · Shift+Enter 换行</small></div><div class="composer-box"><el-input v-model="question" type="textarea" :rows="2" maxlength="2000" show-word-limit :disabled="streaming" placeholder="描述你遇到的故障现象..." @keydown.enter="handleEnter" /><el-button type="primary" :disabled="!question.trim() || streaming" :loading="streaming" @click="sendQuestion"><Send :size="16" />发送</el-button></div></div>
      </main>
    </div>
    <el-dialog v-model="feedbackDialog" title="告诉我们哪里不对" width="440px" :close-on-click-modal="false"><el-form ref="feedbackForm" :model="{ reason: feedbackReason }" :rules="feedbackRules" label-position="top"><el-form-item label="点踩原因" prop="reason"><el-input v-model="feedbackReason" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="请描述答案的问题，帮助管理员改进知识库" /></el-form-item></el-form><template #footer><el-button @click="feedbackDialog = false">取消</el-button><el-button type="primary" :loading="feedbackSubmitting" @click="submitDislike">提交反馈</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.qa-page{min-height:100vh;color:#dce8e8;background:#0d171d}.topbar{height:68px;display:flex;align-items:center;justify-content:space-between;padding:0 42px;border-bottom:1px solid rgba(255,255,255,.07);background:rgba(10,20,25,.9)}.brand{display:flex;align-items:center;gap:10px;color:#d9e9e5;font:600 15px 'Noto Serif SC',serif}.brand-mark{width:31px;height:31px;display:grid;place-items:center;border-radius:8px;background:#178d83;color:#e5fffa;font-weight:700}.topbar-user{display:flex;align-items:center;gap:10px;color:#a9bdbc;font-size:13px}.topbar-user :deep(.el-tag){border:0;background:rgba(45,190,143,.13);color:#55d5ae}.topbar-user button{display:grid;place-items:center;border:0;background:transparent;color:#718787;cursor:pointer;margin-left:7px}.qa-shell{height:calc(100vh - 68px);display:flex;max-width:1500px;margin:0 auto}.session-sidebar{width:270px;flex-shrink:0;padding:24px 16px;border-right:1px solid rgba(255,255,255,.07);background:rgba(12,24,29,.65)}.new-session{width:100%;height:40px;display:flex;align-items:center;justify-content:center;gap:8px;border:1px solid rgba(45,212,191,.4);border-radius:8px;background:rgba(45,212,191,.09);color:#62d8ca;cursor:pointer;font-size:13px}.new-session:hover{background:rgba(45,212,191,.16)}.session-label{display:flex;align-items:center;gap:7px;color:#718889;font-size:11px;margin:28px 8px 10px}.session-list{display:flex;flex-direction:column;gap:4px;overflow-y:auto;max-height:calc(100vh - 190px)}.session-item{width:100%;display:flex;flex-direction:column;gap:6px;text-align:left;border:0;border-left:2px solid transparent;border-radius:6px;background:transparent;color:#9bb0ae;padding:11px 11px;cursor:pointer}.session-item:hover{background:rgba(255,255,255,.04);color:#d8e7e4}.session-item.active{background:rgba(45,212,191,.09);border-left-color:#35b8a8;color:#ddf5f0}.session-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.session-item small{color:#617b7c;font-size:10px}.session-loading,.session-error{color:#718889;font-size:11px;padding:22px 8px;text-align:center}.session-error p{margin:0 0 5px}.chat-main{min-width:0;flex:1;display:flex;flex-direction:column;padding:0 42px}.chat-heading{height:88px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.07)}.chat-kicker{color:#36b7aa;font:500 10px 'DM Mono',monospace;letter-spacing:1.3px}.chat-heading h1{font:600 20px 'Noto Serif SC',serif;color:#eff8f5;margin:6px 0 0;max-width:600px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.chat-state{color:#667e7f;font-size:11px}.chat-state.active{color:#43cabb}.messages-area{flex:1;overflow-y:auto;padding:28px max(0px, calc((100% - 900px)/2)) 22px}.message-loading{text-align:center;color:#718889;font-size:12px;padding:40px}.message-row{display:flex;gap:10px;max-width:920px;margin:0 auto 24px;align-items:flex-start}.message-row.user{flex-direction:row-reverse}.message-avatar{width:28px;height:28px;flex:0 0 28px;display:grid;place-items:center;border-radius:8px;background:rgba(45,212,191,.13);border:1px solid rgba(45,212,191,.22);color:#5bd2c4;font-size:11px}.message-row.user .message-avatar{background:rgba(59,130,246,.13);border-color:rgba(59,130,246,.22);color:#84b9ff}.message-content{max-width:min(780px,85%)}.message-bubble{white-space:pre-wrap;line-height:1.75;font-size:14px;color:#d8e7e4;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:4px 12px 12px 12px;padding:15px 17px}.message-row.user .message-bubble{background:#176e6a;border:0;color:#f0fffc;border-radius:12px 4px 12px 12px}.message-time{display:block;color:#587171;font-size:10px;margin-top:5px;text-align:right}.typing-cursor{display:inline-block;width:2px;height:16px;background:#42c9ba;vertical-align:-3px;margin-left:4px;animation:blink 1s steps(2) infinite}.citations{border-top:1px solid rgba(255,255,255,.08);margin-top:14px;padding-top:12px}.citations-title{color:#77aaa4;font-size:11px;margin-bottom:8px}.citation-card{display:flex;gap:8px;padding:9px;background:rgba(0,0,0,.16);border:1px solid rgba(255,255,255,.06);border-radius:6px;margin-top:6px}.citation-index{color:#40c3b4;font:11px 'DM Mono',monospace}.citation-card strong{display:block;color:#cfe2df;font-size:11px}.citation-card small{display:block;color:#5fa19a;font-size:10px;margin-top:3px}.citation-card p{color:#819997;font-size:11px;line-height:1.55;margin:5px 0 0}.feedback-row{display:flex;align-items:center;gap:5px;border-top:1px solid rgba(255,255,255,.07);margin-top:12px;padding-top:9px}.feedback-row button{width:26px;height:25px;display:grid;place-items:center;border:0;border-radius:5px;background:transparent;color:#718787;cursor:pointer}.feedback-row button:hover,.feedback-row button.selected{background:rgba(45,212,191,.13);color:#55d5ae}.feedback-row span{color:#587171;font-size:10px;margin-left:auto}.blocked-message,.failed-message{padding:14px 16px;border-radius:8px;font-size:13px;line-height:1.7}.blocked-message{color:#f3c27a;background:rgba(235,158,65,.1);border:1px solid rgba(235,158,65,.2)}.blocked-message strong{display:block;margin-bottom:3px}.failed-message{color:#ff9a91;background:rgba(245,104,94,.1);border:1px solid rgba(245,104,94,.2)}.composer{border-top:1px solid rgba(255,255,255,.07);padding:15px max(0px, calc((100% - 900px)/2)) 22px}.composer-tools{display:flex;align-items:center;gap:9px;margin-bottom:9px;color:#718889;font-size:11px}.composer-tools :deep(.el-select){width:145px}.composer-tools :deep(.el-select__wrapper){min-height:30px;background:rgba(255,255,255,.035);box-shadow:0 0 0 1px rgba(255,255,255,.08) inset}.composer-tools small{color:#526c6c;margin-left:auto}.composer-box{display:flex;gap:10px;align-items:flex-end}.composer-box :deep(.el-textarea__inner){resize:none;color:#d9e8e5;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);box-shadow:none;border-radius:8px;padding:12px 13px}.composer-box :deep(.el-textarea__inner:focus){border-color:rgba(45,212,191,.5)}.composer-box :deep(.el-button){height:42px;border:0;background:#1e9e91;border-radius:7px;padding:0 18px}.composer-box :deep(.el-button .lucide){margin-right:6px;vertical-align:-3px}.qa-page :deep(.el-dialog){background:#122127;border:1px solid rgba(143,190,185,.16)}.qa-page :deep(.el-dialog__title){color:#eaf5f2}.qa-page :deep(.el-form-item__label){color:#8ba1a0;font-size:12px}.qa-page :deep(.el-textarea__inner){background:rgba(5,14,18,.55);color:#dce8e5;box-shadow:0 0 0 1px rgba(140,183,179,.16) inset}.qa-page :deep(.el-alert){margin-bottom:16px}@keyframes blink{50%{opacity:0}}@media(max-width:800px){.topbar{padding:0 18px}.topbar-user span,.topbar-user :deep(.el-tag){display:none}.session-sidebar{width:220px}.chat-main{padding:0 18px}.chat-heading h1{font-size:17px}.composer-tools small{display:none}}@media(max-width:600px){.qa-shell{height:calc(100vh - 60px)}.topbar{height:60px}.session-sidebar{width:72px;padding:18px 10px}.new-session{font-size:0}.new-session .lucide{margin:0}.session-label{justify-content:center}.session-label{font-size:0}.session-item{padding:12px 8px}.session-title{font-size:0}.session-item small{display:none}.chat-main{padding:0 12px}.chat-heading{height:76px}.chat-state{display:none}.message-content{max-width:86%}.composer{padding-bottom:12px}.composer-tools{flex-wrap:wrap}.composer-box :deep(.el-button){padding:0 13px}.composer-box :deep(.el-button span){display:none}}
</style>
<style scoped>
.qa-page{height:100%;min-height:0}.qa-shell{height:100%;max-width:none;margin:0}
</style>
