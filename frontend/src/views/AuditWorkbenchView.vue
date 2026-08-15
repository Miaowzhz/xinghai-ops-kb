<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ClipboardCheck, Eye, FileCheck2, Plus, RefreshCw, ShieldCheck } from '@lucide/vue'
import { useAuthStore } from '../stores/auth'
import { getAuditTaskDetail, getAuditTasks, resolveAuditTask } from '../api/audit'
import { createGuardrailRule, getGuardrailRules, updateGuardrailRule } from '../api/guardrail'

const auth = useAuthStore()
const activeTab = ref('tasks')
const permissionDenied = ref(false)
const isNarrow = ref(window.innerWidth < 768)

const tasks = ref([])
const taskStatus = ref('pending')
const taskPage = ref(1)
const taskPageSize = 20
const taskTotal = ref(0)
const taskLoading = ref(false)
const taskError = ref(false)
const detailLoadingId = ref(null)
const drawerVisible = ref(false)
const taskDetail = ref(null)
const resolving = ref(false)
const reviewFormRef = ref()
const reviewForm = reactive({ status: '', resolution: '' })

const rules = ref([])
const rulesLoaded = ref(false)
const rulesLoading = ref(false)
const rulesError = ref(false)
const switchingRuleId = ref(null)
const ruleDialogVisible = ref(false)
const ruleSaving = ref(false)
const editingRuleId = ref(null)
const ruleFormRef = ref()
const ruleForm = reactive(defaultRuleForm())

const taskStatuses = [
  { value: 'pending', label: '待处理' },
  { value: 'resolved', label: '已解决' },
  { value: 'rejected', label: '已驳回' },
  { value: '', label: '全部' },
]
const statusMeta = {
  pending: { label: '待处理', type: 'warning' },
  resolved: { label: '已解决', type: 'success' },
  rejected: { label: '已驳回', type: 'info' },
}
const messageStatusMeta = {
  normal: { label: '正常', type: 'success' },
  blocked: { label: '护栏拦截', type: 'danger' },
  refused: { label: '无依据拒答', type: 'warning' },
  failed: { label: '系统失败', type: 'info' },
}
const ruleTypeMeta = {
  sensitive_op: { label: '敏感操作', type: 'primary' },
  high_risk_cmd: { label: '高危命令', type: 'danger' },
  price: { label: '价格商务', type: 'warning' },
}
const actionMeta = {
  block: { label: '直接拦截', type: 'danger' },
  confirm: { label: '提示确认', type: 'warning' },
}
const matchTypeLabels = { keyword: '关键词', regex: '正则' }
const reviewRules = {
  status: [{ required: true, message: '请选择结论类型', trigger: 'change' }],
  resolution: [
    { required: true, message: '请填写处理结论', trigger: 'blur' },
    { min: 1, max: 1000, message: '处理结论需在 1-1000 字之间', trigger: 'blur' },
  ],
}
const ruleFormRules = {
  rule_name: [{ required: true, message: '请填写规则名', trigger: 'blur' }, { min: 1, max: 64, message: '规则名需在 1-64 字之间', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  action: [{ required: true, message: '请选择命中动作', trigger: 'change' }],
  match_type: [{ required: true, message: '请选择匹配方式', trigger: 'change' }],
  pattern: [
    { required: true, message: '请填写匹配内容', trigger: 'blur' },
    { min: 1, max: 512, message: '匹配内容需在 1-512 字之间', trigger: 'blur' },
    { validator: validatePattern, trigger: 'blur' },
  ],
  reply_text: [{ required: true, message: '请填写命中后回复话术', trigger: 'blur' }],
}

const drawerSize = computed(() => isNarrow.value ? '100%' : 'min(680px, 56%)')
const selectedStatusMeta = computed(() => statusMeta[taskDetail.value?.status] || statusMeta.pending)
const selectedMessageMeta = computed(() => messageStatusMeta[taskDetail.value?.message_status] || messageStatusMeta.normal)
const taskEmptyText = computed(() => taskStatus.value === 'pending' ? '当前没有待处理的审核任务' : '当前筛选下没有审核任务')

function defaultRuleForm() {
  return { rule_name: '', rule_type: '', action: '', match_type: 'keyword', pattern: '', reply_text: '', enabled: true }
}

function validatePattern(rule, value, callback) {
  if (ruleForm.match_type !== 'regex' || !value) return callback()
  try { new RegExp(value); callback() } catch { callback(new Error('正则表达式格式不正确')) }
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replaceAll('/', '-')
}

function updateViewport() { isNarrow.value = window.innerWidth < 768 }

async function loadTasks() {
  taskLoading.value = true
  taskError.value = false
  try {
    const params = { page: taskPage.value, page_size: taskPageSize }
    if (taskStatus.value) params.status = taskStatus.value
    const response = await getAuditTasks(params)
    tasks.value = response.items || []
    taskTotal.value = response.total || 0
  } catch (error) {
    if (error.response?.status === 403) permissionDenied.value = true
    else taskError.value = true
  } finally {
    taskLoading.value = false
  }
}

function changeTaskStatus() { taskPage.value = 1; loadTasks() }
function changeTaskPage(value) { taskPage.value = value; loadTasks() }

async function openTask(row) {
  detailLoadingId.value = row.id
  try {
    taskDetail.value = await getAuditTaskDetail(row.id)
    reviewForm.status = row.status === 'pending' ? '' : row.status
    reviewForm.resolution = taskDetail.value.resolution || ''
    drawerVisible.value = true
    await nextTick()
    reviewFormRef.value?.clearValidate()
  } catch (error) {
    if (error.response?.status === 404) {
      ElMessage.error('任务不存在或已被删除')
      loadTasks()
    } else if (error.response?.status === 403) permissionDenied.value = true
    else ElMessage.error('详情加载失败，请重试')
  } finally {
    detailLoadingId.value = null
  }
}

async function submitResolution() {
  try { await reviewFormRef.value.validate() } catch { return }
  resolving.value = true
  try {
    await resolveAuditTask(taskDetail.value.id, { status: reviewForm.status, resolution: reviewForm.resolution.trim() })
    ElMessage.success('处理完成')
    drawerVisible.value = false
    await loadTasks()
  } catch (error) {
    if (error.response?.status === 409) {
      await ElMessageBox.alert('任务已被处理，请刷新查看最新状态', '状态已变更', { confirmButtonText: '知道了', type: 'warning' })
      drawerVisible.value = false
      await loadTasks()
    } else ElMessage.error('提交失败，请稍后重试')
  } finally {
    resolving.value = false
  }
}

async function loadRules() {
  rulesLoading.value = true
  rulesError.value = false
  try {
    rules.value = await getGuardrailRules()
    rulesLoaded.value = true
  } catch (error) {
    if (error.response?.status === 403) permissionDenied.value = true
    else rulesError.value = true
  } finally {
    rulesLoading.value = false
  }
}

function handleTabChange(name) {
  if (name === 'rules' && !rulesLoaded.value) loadRules()
}

function openRuleDialog(rule = null) {
  editingRuleId.value = rule?.id || null
  Object.assign(ruleForm, rule ? {
    rule_name: rule.rule_name,
    rule_type: rule.rule_type,
    action: rule.action,
    match_type: rule.match_type,
    pattern: rule.pattern,
    reply_text: rule.reply_text,
    enabled: rule.enabled,
  } : defaultRuleForm())
  ruleDialogVisible.value = true
  nextTick(() => ruleFormRef.value?.clearValidate())
}

async function saveRule() {
  try { await ruleFormRef.value.validate() } catch { return }
  ruleSaving.value = true
  const payload = { ...ruleForm, rule_name: ruleForm.rule_name.trim(), pattern: ruleForm.pattern.trim(), reply_text: ruleForm.reply_text.trim() }
  try {
    if (editingRuleId.value) {
      await updateGuardrailRule(editingRuleId.value, payload)
      ElMessage.success('规则已更新')
    } else {
      await createGuardrailRule(payload)
      ElMessage.success('规则已新增')
    }
    ruleDialogVisible.value = false
    await loadRules()
  } catch (error) {
    if (error.response?.status === 404) { ElMessage.error('规则不存在'); ruleDialogVisible.value = false; await loadRules() }
    else ElMessage.error(error.response?.data?.detail || (editingRuleId.value ? '更新失败，请稍后重试' : '新增失败，请稍后重试'))
  } finally {
    ruleSaving.value = false
  }
}

async function toggleRule(row, enabled) {
  switchingRuleId.value = row.id
  try {
    await updateGuardrailRule(row.id, { enabled })
    ElMessage.success(enabled ? '已启用' : '已停用')
  } catch (error) {
    row.enabled = !enabled
    if (error.response?.status === 404) { ElMessage.error('规则不存在'); await loadRules() }
    else ElMessage.error('状态更新失败')
  } finally {
    switchingRuleId.value = null
  }
}

onMounted(() => {
  window.addEventListener('resize', updateViewport)
  if (!auth.isAdmin) permissionDenied.value = true
  else loadTasks()
})
onUnmounted(() => window.removeEventListener('resize', updateViewport))
</script>

<template>
  <main class="audit-page">
    <header class="audit-heading">
      <div>
        <span class="heading-kicker">反馈进化</span>
        <h1>反馈审核工作台</h1>
        <p>审查低评回答，维护问答护栏。</p>
      </div>
      <div class="admin-mark"><ClipboardCheck :size="17" /><span>当前管理员</span><strong>{{ auth.user?.display_name || '管理员' }}</strong></div>
    </header>

    <el-result v-if="permissionDenied" icon="error" title="无权限" sub-title="本页面仅知识管理员可用" class="permission-result" />

    <el-tabs v-else v-model="activeTab" class="workbench-tabs" @tab-change="handleTabChange">
      <el-tab-pane name="tasks">
        <template #label><span class="tab-label"><FileCheck2 :size="16" />审核任务</span></template>
        <section class="workspace-panel">
          <div class="panel-toolbar">
            <div class="toolbar-filter"><span>状态</span><el-select v-model="taskStatus" @change="changeTaskStatus"><el-option v-for="item in taskStatuses" :key="item.value" :label="item.label" :value="item.value" /></el-select></div>
            <div class="record-count">共 <strong>{{ taskTotal }}</strong> 条</div>
          </div>

          <el-alert v-if="taskError" title="审核任务加载失败" type="error" show-icon :closable="false" class="list-error"><el-button text type="danger" @click="loadTasks"><RefreshCw :size="14" />重新加载</el-button></el-alert>
          <div v-loading="taskLoading" class="table-scroll">
            <el-table v-if="!taskError" :data="tasks" class="audit-table" row-key="id">
              <el-table-column prop="id" label="任务 ID" width="105"><template #default="{ row }"><span class="mono-id">#{{ row.id }}</span></template></el-table-column>
              <el-table-column prop="message_id" label="回答 ID" width="110"><template #default="{ row }">{{ row.message_id }}</template></el-table-column>
              <el-table-column label="状态" width="115"><template #default="{ row }"><el-tag :type="(statusMeta[row.status] || statusMeta.pending).type" effect="dark">{{ (statusMeta[row.status] || statusMeta.pending).label }}</el-tag></template></el-table-column>
              <el-table-column label="处理结论" min-width="280"><template #default="{ row }"><el-tooltip v-if="row.resolution" :content="row.resolution" placement="top"><span class="ellipsis">{{ row.resolution }}</span></el-tooltip><span v-else class="muted">待管理员处理</span></template></el-table-column>
              <el-table-column label="创建时间" width="165"><template #default="{ row }">{{ formatDateTime(row.created_at) }}</template></el-table-column>
              <el-table-column label="处理时间" width="165"><template #default="{ row }">{{ formatDateTime(row.resolved_at) }}</template></el-table-column>
              <el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button link :type="row.status === 'pending' ? 'primary' : 'info'" :loading="detailLoadingId === row.id" @click="openTask(row)"><Eye :size="14" />{{ row.status === 'pending' ? '处理' : '查看' }}</el-button></template></el-table-column>
              <template #empty><el-empty :image-size="72" :description="taskEmptyText" /></template>
            </el-table>
          </div>
          <div class="pagination-row"><el-pagination v-model:current-page="taskPage" :page-size="taskPageSize" :total="taskTotal" layout="total, prev, pager, next" @current-change="changeTaskPage" /></div>
        </section>
      </el-tab-pane>

      <el-tab-pane name="rules">
        <template #label><span class="tab-label"><ShieldCheck :size="16" />护栏规则</span></template>
        <section class="workspace-panel">
          <div class="panel-toolbar rule-toolbar"><div><h2>规则库</h2><p>启用的规则会参与每次问答的安全检查。</p></div><el-button type="primary" @click="openRuleDialog()"><Plus :size="16" />新增规则</el-button></div>
          <el-alert v-if="rulesError" title="护栏规则加载失败" type="error" show-icon :closable="false" class="list-error"><el-button text type="danger" @click="loadRules"><RefreshCw :size="14" />重新加载</el-button></el-alert>
          <div v-loading="rulesLoading" class="table-scroll">
            <el-table v-if="!rulesError" :data="rules" class="audit-table rules-table" row-key="id">
              <el-table-column prop="rule_name" label="规则名" min-width="190" />
              <el-table-column label="类型" width="120"><template #default="{ row }"><el-tag :type="(ruleTypeMeta[row.rule_type] || {}).type" effect="dark">{{ (ruleTypeMeta[row.rule_type] || {}).label || row.rule_type }}</el-tag></template></el-table-column>
              <el-table-column label="动作" width="115"><template #default="{ row }"><el-tag :type="(actionMeta[row.action] || {}).type" effect="dark">{{ (actionMeta[row.action] || {}).label || row.action }}</el-tag></template></el-table-column>
              <el-table-column label="匹配" width="95"><template #default="{ row }">{{ matchTypeLabels[row.match_type] || row.match_type }}</template></el-table-column>
              <el-table-column label="匹配内容" min-width="210"><template #default="{ row }"><code class="pattern-code">{{ row.pattern }}</code></template></el-table-column>
              <el-table-column label="回复话术" min-width="260"><template #default="{ row }"><el-tooltip :content="row.reply_text" placement="top"><span class="ellipsis">{{ row.reply_text }}</span></el-tooltip></template></el-table-column>
              <el-table-column label="启用" width="90"><template #default="{ row }"><el-switch v-model="row.enabled" :loading="switchingRuleId === row.id" @change="value => toggleRule(row, value)" /></template></el-table-column>
              <el-table-column label="操作" width="80" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openRuleDialog(row)">编辑</el-button></template></el-table-column>
              <template #empty><el-empty :image-size="72" description="还没有护栏规则" /></template>
            </el-table>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="drawerVisible" :size="drawerSize" destroy-on-close class="audit-drawer">
      <template #header><div class="drawer-heading"><div><span>审核任务</span><h2>#{{ taskDetail?.id }}</h2></div><el-tag v-if="taskDetail" :type="selectedStatusMeta.type" effect="dark">{{ selectedStatusMeta.label }}</el-tag></div></template>
      <template v-if="taskDetail">
        <section class="context-section"><div class="section-label">01 原始问题</div><div class="question-block">{{ taskDetail.question }}</div></section>
        <section class="context-section"><div class="section-label">02 系统回答</div><div class="answer-block"><el-tag :type="selectedMessageMeta.type" effect="dark" size="small">{{ selectedMessageMeta.label }}</el-tag><p>{{ taskDetail.answer }}</p></div></section>
        <section class="context-section"><div class="section-label">03 引用快照</div><el-alert v-if="taskDetail.document_deleted" title="关联文档已被删除，以下为当时留存的引用快照" type="warning" show-icon :closable="false" /><div v-if="taskDetail.citations?.length" class="citation-list"><article v-for="(citation, index) in taskDetail.citations" :key="citation.chunk_id || index" class="audit-citation"><span class="citation-index">{{ String(index + 1).padStart(2, '0') }}</span><div><div class="citation-title"><strong>{{ citation.document_title }}</strong><el-tag size="small" effect="plain">{{ citation.product_version }}</el-tag></div><small>{{ citation.product_line }}</small><p>{{ citation.snippet }}</p></div></article></div><div v-else class="empty-inline">无引用快照</div></section>
        <section class="context-section"><div class="section-label">04 点踩原因</div><el-alert :title="taskDetail.dislike_reason || '用户未填写原因'" type="error" show-icon :closable="false" /></section>
        <section class="resolution-section"><div class="section-label">05 处理结论</div><el-form v-if="taskDetail.status === 'pending'" ref="reviewFormRef" :model="reviewForm" :rules="reviewRules" label-position="top"><el-form-item label="结论类型" prop="status"><el-radio-group v-model="reviewForm.status"><el-radio value="resolved">已解决</el-radio><el-radio value="rejected">已驳回</el-radio></el-radio-group></el-form-item><el-form-item label="处理结论" prop="resolution"><el-input v-model="reviewForm.resolution" type="textarea" :rows="5" maxlength="1000" show-word-limit placeholder="请说明处理方式与依据，例如：已重新上传 V3.2 新版 SOP 并重新入库" /></el-form-item><div class="submit-row"><el-button type="primary" :loading="resolving" @click="submitResolution">提交处理结论</el-button></div></el-form><div v-else class="resolved-summary"><div><span>结论类型</span><el-tag :type="selectedStatusMeta.type" effect="dark">{{ selectedStatusMeta.label }}</el-tag></div><div><span>处理时间</span><strong>{{ formatDateTime(taskDetail.resolved_at) }}</strong></div><p>{{ taskDetail.resolution }}</p></div></section>
      </template>
    </el-drawer>

    <el-dialog v-model="ruleDialogVisible" :title="editingRuleId ? '编辑护栏规则' : '新增护栏规则'" width="min(560px, calc(100vw - 28px))" :close-on-click-modal="false" class="rule-dialog">
      <el-form ref="ruleFormRef" :model="ruleForm" :rules="ruleFormRules" label-position="top">
        <el-form-item label="规则名" prop="rule_name"><el-input v-model="ruleForm.rule_name" maxlength="64" placeholder="例如：生产环境高危命令拦截" /></el-form-item>
        <div class="form-grid"><el-form-item label="规则类型" prop="rule_type"><el-select v-model="ruleForm.rule_type" class="full-width"><el-option label="敏感操作" value="sensitive_op" /><el-option label="高危命令" value="high_risk_cmd" /><el-option label="价格商务" value="price" /></el-select></el-form-item><el-form-item label="命中动作" prop="action"><el-select v-model="ruleForm.action" class="full-width"><el-option label="直接拦截" value="block" /><el-option label="提示确认" value="confirm" /></el-select></el-form-item></div>
        <el-form-item label="匹配方式" prop="match_type"><el-segmented v-model="ruleForm.match_type" :options="[{ label: '关键词包含', value: 'keyword' }, { label: '正则表达式', value: 'regex' }]" /></el-form-item>
        <el-form-item label="匹配内容" prop="pattern"><el-input v-model="ruleForm.pattern" maxlength="512" :placeholder="ruleForm.match_type === 'regex' ? '如：rm\\s+-rf' : '如：rm -rf'" /><div v-if="ruleForm.match_type === 'regex'" class="field-hint">请确认正则写法正确，写错的规则会被系统跳过</div></el-form-item>
        <el-form-item label="命中后回复话术" prop="reply_text"><el-input v-model="ruleForm.reply_text" type="textarea" :rows="4" placeholder="该操作属于高危命令，请提交变更工单" /></el-form-item>
        <el-form-item label="规则状态"><el-switch v-model="ruleForm.enabled" active-text="启用" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="ruleDialogVisible = false">取消</el-button><el-button type="primary" :loading="ruleSaving" @click="saveRule">{{ editingRuleId ? '保存修改' : '新增规则' }}</el-button></template>
    </el-dialog>
  </main>
</template>

<style scoped>
.audit-page{min-height:100%;color:#dce8e8;background:#0d171d;padding:30px 36px 56px}.audit-heading{max-width:1360px;margin:0 auto 20px;display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.heading-kicker{color:#36b7aa;font:500 10px 'DM Mono',monospace;letter-spacing:1.4px}.audit-heading h1{margin:7px 0 0;color:#eff8f5;font:600 28px 'Noto Serif SC',serif}.audit-heading p{margin:7px 0 0;color:#708788;font-size:12px}.admin-mark{display:flex;align-items:center;gap:7px;color:#667f80;font-size:10px}.admin-mark svg{color:#3dbbad}.admin-mark strong{color:#b9cfcb;font-size:12px}.permission-result{max-width:1000px;margin:50px auto;background:rgba(16,30,36,.82);border:1px solid rgba(255,255,255,.08)}.workbench-tabs{max-width:1360px;margin:0 auto}.workbench-tabs :deep(.el-tabs__header){margin:0}.workbench-tabs :deep(.el-tabs__nav-wrap::after){height:1px;background:rgba(255,255,255,.08)}.workbench-tabs :deep(.el-tabs__item){height:48px;color:#708687;font-size:12px}.workbench-tabs :deep(.el-tabs__item.is-active){color:#53cdbf}.workbench-tabs :deep(.el-tabs__active-bar){height:2px;background:#35b8a8}.tab-label{display:flex;align-items:center;gap:7px}.workspace-panel{margin-top:18px;padding:20px 22px 16px;border:1px solid rgba(143,190,185,.13);border-radius:8px;background:rgba(16,30,36,.88);box-shadow:0 20px 50px rgba(0,0,0,.13)}.panel-toolbar{min-height:40px;display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.toolbar-filter{display:flex;align-items:center;gap:10px;color:#789091;font-size:11px}.toolbar-filter :deep(.el-select){width:150px}.toolbar-filter :deep(.el-select__wrapper){background:rgba(5,14,18,.55);box-shadow:0 0 0 1px rgba(140,183,179,.16) inset}.record-count{color:#657d7e;font-size:11px}.record-count strong{color:#4bc6b8;font:500 13px 'DM Mono',monospace}.rule-toolbar h2{margin:0;color:#dcebe8;font:600 16px 'Noto Serif SC',serif}.rule-toolbar p{margin:5px 0 0;color:#637b7c;font-size:10px}.rule-toolbar :deep(.el-button--primary),.submit-row :deep(.el-button--primary){border:0;background:#1e9e91}.rule-toolbar :deep(.el-button .lucide){margin-right:6px;vertical-align:-3px}.list-error{margin-bottom:16px;background:rgba(185,59,60,.1)}.list-error :deep(.el-button .lucide){margin-right:5px;vertical-align:-3px}.table-scroll{overflow-x:auto;min-height:320px}.audit-table{min-width:960px;--el-table-bg-color:transparent;--el-table-tr-bg-color:transparent;--el-table-header-bg-color:rgba(255,255,255,.035);--el-table-row-hover-bg-color:rgba(45,212,191,.045);--el-table-border-color:rgba(255,255,255,.07);--el-table-text-color:#b9cbca;--el-table-header-text-color:#718889}.rules-table{min-width:1250px}.audit-table :deep(.el-table__header th){height:43px;font-size:11px;font-weight:500}.audit-table :deep(.el-table__row td){height:58px;font-size:11px}.audit-table :deep(.el-tag){min-width:56px;justify-content:center;border:0}.audit-table :deep(.el-tag--warning){background:rgba(237,160,70,.13);color:#f5be73}.audit-table :deep(.el-tag--success){background:rgba(45,190,143,.13);color:#55d5ae}.audit-table :deep(.el-tag--danger){background:rgba(245,104,94,.13);color:#ff9187}.audit-table :deep(.el-tag--info){background:rgba(145,166,167,.12);color:#94a8a7}.audit-table :deep(.el-tag--primary){background:rgba(80,150,224,.12);color:#83b9ed}.mono-id,.pattern-code{color:#55c7ba;font:11px 'DM Mono',monospace}.pattern-code{display:block;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ellipsis{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.muted{color:#536c6d}.pagination-row{display:flex;justify-content:flex-end;padding-top:16px}.pagination-row :deep(.el-pagination){--el-pagination-bg-color:transparent;--el-pagination-text-color:#829998;--el-pagination-button-color:#829998;--el-pagination-hover-color:#42c9ba}.drawer-heading{width:100%;display:flex;align-items:center;justify-content:space-between;padding-right:12px}.drawer-heading span{color:#617a7b;font-size:10px}.drawer-heading h2{margin:3px 0 0;color:#e5f1ee;font:600 20px 'DM Mono',monospace}.audit-page :deep(.audit-drawer){background:#112027;color:#dce8e5}.audit-page :deep(.audit-drawer .el-drawer__header){margin-bottom:0;padding-bottom:17px;border-bottom:1px solid rgba(255,255,255,.08)}.audit-page :deep(.audit-drawer .el-drawer__body){padding:22px 24px 34px}.context-section{margin-bottom:26px}.section-label{margin-bottom:10px;color:#4abfb2;font:500 10px 'DM Mono',monospace;letter-spacing:.7px}.question-block,.answer-block{border:1px solid rgba(255,255,255,.08);border-radius:7px;background:rgba(255,255,255,.035);padding:14px 16px;color:#d1e1de;font-size:13px;line-height:1.72}.answer-block{position:relative;padding-top:42px;white-space:pre-wrap}.answer-block>.el-tag{position:absolute;right:12px;top:11px;border:0}.answer-block p{margin:0}.context-section :deep(.el-alert){background:rgba(237,160,70,.09);border:1px solid rgba(237,160,70,.15)}.citation-list{margin-top:10px;border-top:1px solid rgba(255,255,255,.07)}.audit-citation{display:grid;grid-template-columns:28px 1fr;gap:9px;padding:13px 2px;border-bottom:1px solid rgba(255,255,255,.06)}.citation-index{color:#3fc0b2;font:10px 'DM Mono',monospace}.citation-title{display:flex;align-items:center;gap:8px}.citation-title strong{color:#ccdfdc;font-size:11px}.citation-title :deep(.el-tag){height:18px;border-color:rgba(45,212,191,.2);color:#69b8af;background:transparent;font-size:9px}.audit-citation small{display:block;margin-top:4px;color:#568d87;font-size:9px}.audit-citation p{margin:6px 0 0;color:#819896;font-size:11px;line-height:1.65}.empty-inline{padding:18px;border:1px dashed rgba(255,255,255,.09);color:#627a7b;text-align:center;font-size:11px}.resolution-section{padding-top:22px;border-top:1px solid rgba(255,255,255,.09)}.resolution-section :deep(.el-form-item__label),.rule-dialog :deep(.el-form-item__label){color:#849c9b;font-size:11px}.resolution-section :deep(.el-textarea__inner),.rule-dialog :deep(.el-input__wrapper),.rule-dialog :deep(.el-textarea__inner),.rule-dialog :deep(.el-select__wrapper){background:rgba(5,14,18,.55);color:#dce8e5;box-shadow:0 0 0 1px rgba(140,183,179,.16) inset}.submit-row{display:flex;justify-content:flex-end}.resolved-summary{display:grid;grid-template-columns:1fr 1fr;gap:12px}.resolved-summary>div{display:flex;align-items:center;justify-content:space-between;color:#687f80;font-size:10px}.resolved-summary strong{color:#b9cecb;font-size:11px}.resolved-summary p{grid-column:1/-1;margin:0;padding:13px 15px;border:1px solid rgba(255,255,255,.08);border-radius:7px;background:rgba(255,255,255,.03);color:#bfcecc;font-size:12px;line-height:1.7}.audit-page :deep(.rule-dialog){background:#122127;border:1px solid rgba(143,190,185,.16)}.audit-page :deep(.rule-dialog .el-dialog__title){color:#e5f0ed;font:600 17px 'Noto Serif SC',serif}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.full-width{width:100%}.field-hint{margin-top:6px;color:#607879;font-size:10px;line-height:1.5}.rule-dialog :deep(.el-segmented){--el-segmented-bg-color:rgba(5,14,18,.55);--el-segmented-item-selected-bg-color:rgba(45,212,191,.14);--el-segmented-item-selected-color:#5dd5c7;width:100%}.rule-dialog :deep(.el-segmented__item){flex:1}.rule-dialog :deep(.el-dialog__footer .el-button--primary){border:0;background:#1e9e91}
@media(max-width:767px){.audit-page{padding:22px 14px 42px}.audit-heading{align-items:flex-start}.audit-heading h1{font-size:23px}.audit-heading p,.admin-mark span{display:none}.admin-mark{padding-top:5px}.workspace-panel{padding:16px 12px 12px}.panel-toolbar{align-items:flex-start;flex-direction:column}.record-count{align-self:flex-end}.rule-toolbar{flex-direction:row;align-items:center}.rule-toolbar p{display:none}.audit-page :deep(.audit-drawer .el-drawer__body){padding:18px 14px 28px}.form-grid{grid-template-columns:1fr}.resolved-summary{grid-template-columns:1fr}.resolved-summary p{grid-column:auto}}
</style>
