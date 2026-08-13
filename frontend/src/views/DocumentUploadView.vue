<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, CloudUpload, FileText, RefreshCw, Upload, X } from '@lucide/vue'
import { useAuthStore } from '../stores/auth'
import { getDocumentDetail, getDocumentList, uploadDocument } from '../api/document'

const router = useRouter()
const auth = useAuthStore()
const uploadRef = ref()
const formRef = ref()
const file = ref(null)
const documents = ref([])
const loading = ref(false)
const submitting = ref(false)
const polling = ref(false)
const firstLoadError = ref(false)
const permissionDenied = ref(false)
const expandedReasons = reactive({})
let pollTimer = null
let warningShown = false

const form = reactive({ title: '', doc_type: 'sop', product_line: '', product_version: '' })
const docTypes = [
  { value: 'manual', label: '产品手册' },
  { value: 'case', label: '故障案例' },
  { value: 'sop', label: '运维 SOP' },
  { value: 'api', label: 'API 文档' },
]
const typeLabels = Object.fromEntries(docTypes.map(item => [item.value, item.label]))
const terminalStatuses = new Set(['success', 'failed'])
const activeCount = computed(() => documents.value.filter(item => !terminalStatuses.has(item.status)).length)
const expandedRowKeys = computed(() => documents.value.filter(item => item.status === 'failed').map(item => item.id))
const rules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }, { min: 1, max: 255, message: '标题长度为 1-255 个字符', trigger: 'blur' }],
  doc_type: [{ required: true, message: '请选择文档类型', trigger: 'change' }],
  product_line: [{ required: true, message: '请输入产品线', trigger: 'blur' }, { min: 1, max: 64, message: '产品线长度为 1-64 个字符', trigger: 'blur' }],
  product_version: [{ required: true, message: '请输入产品版本', trigger: 'blur' }, { min: 1, max: 32, message: '产品版本长度为 1-32 个字符', trigger: 'blur' }],
}

function isAllowed(fileItem) {
  return ['pdf', 'docx', 'md', 'txt'].includes(fileItem.name.split('.').pop()?.toLowerCase())
}
function handleFileChange(uploadFile) {
  if (!isAllowed(uploadFile)) {
    ElMessage.warning('仅支持 PDF / DOCX / MD / TXT 格式')
    clearFile()
    return
  }
  file.value = uploadFile.raw
  if (!form.title) form.title = uploadFile.name.replace(/\.[^.]+$/, '')
}
function handleFileExceed() { ElMessage.info('一次只能上传一个文档') }
function clearFile() { file.value = null; uploadRef.value?.clearFiles() }
function resetForm() {
  clearFile(); form.title = ''; form.doc_type = 'sop'; form.product_line = ''; form.product_version = ''; formRef.value?.clearValidate()
}
function formatTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = number => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
function statusLabel(status) { return { pending: '待入库', parsing: '入库中', success: '成功', failed: '失败' }[status] || status }
function statusType(status) { return { pending: 'info', parsing: '', success: 'success', failed: 'danger' }[status] || 'info' }

async function loadDocuments({ initial = false } = {}) {
  if (initial) loading.value = true
  try {
    const data = await getDocumentList({ page: 1, page_size: 20 })
    documents.value = data.items || []
    firstLoadError.value = false
    await loadFailureReasons()
    if (documents.value.some(item => !terminalStatuses.has(item.status))) startPolling()
    else stopPolling()
  } catch (error) {
    if (error.response?.status === 403) permissionDenied.value = true
    if (initial) firstLoadError.value = true
    if (!initial && !warningShown) {
      warningShown = true
      ElMessage.warning('进度刷新失败，将在 3 秒后重试')
      setTimeout(() => { warningShown = false }, 3000)
    }
    console.error('加载文档进度失败', error)
  } finally { loading.value = false }
}
async function loadFailureReasons() {
  await Promise.all(documents.value.filter(item => item.status === 'failed').map(async item => {
    if (expandedReasons[item.id]) return
    try {
      const detail = await getDocumentDetail(item.id)
      expandedReasons[item.id] = detail.fail_reason || '入库失败，请重试'
    } catch (error) {
      expandedReasons[item.id] = '入库失败，请重试'
      if (error.response?.status === 403) permissionDenied.value = true
    }
  }))
}
function startPolling() {
  if (pollTimer || permissionDenied.value) return
  polling.value = true
  pollTimer = window.setInterval(() => loadDocuments(), 3000)
}
function stopPolling() {
  if (pollTimer) window.clearInterval(pollTimer)
  pollTimer = null; polling.value = false
}
async function submit() {
  if (!file.value) { ElMessage.warning('必须先选择文件'); return }
  await formRef.value.validate(async valid => {
    if (!valid) return
    submitting.value = true
    const formData = new FormData()
    formData.append('file', file.value)
    Object.entries(form).forEach(([key, value]) => formData.append(key, value.trim()))
    try {
      await uploadDocument(formData)
      ElMessage.success('上传成功，已开始入库')
      resetForm(); await loadDocuments(); startPolling()
    } catch (error) {
      if (error.response?.status === 403) permissionDenied.value = true
      ElMessage.error(error.response?.data?.detail || '上传失败，请稍后重试')
    } finally { submitting.value = false }
  })
}
onMounted(() => { if (!auth.isAdmin) permissionDenied.value = true; else loadDocuments({ initial: true }) })
onUnmounted(stopPolling)
</script>

<template>
  <div class="document-page">
    <div class="page-grid">
      <header class="page-header">
        <button class="back-button" title="返回工作台" @click="router.push('/workspace')"><ArrowLeft :size="18" /></button>
        <div><div class="eyebrow">KNOWLEDGE INGESTION / P04</div><h1>文档上传与入库进度</h1><p>把可靠的运维经验，变成下一次排障可检索的答案。</p></div>
        <div class="admin-chip"><span class="admin-avatar">{{ auth.user?.display_name?.charAt(0) || '管' }}</span><span><small>知识管理员</small>{{ auth.user?.display_name || '管理员' }}</span></div>
      </header>

      <el-result v-if="permissionDenied" icon="error" title="无权限" sub-title="本页面仅知识管理员可用" class="permission-result" />
      <template v-else>
        <section class="upload-panel panel">
          <div class="panel-heading"><div><span class="section-index">01</span><div><h2>上传新文档</h2><p>填写元信息，让后续检索更准确</p></div></div><span class="required-note"><i></i> 必填信息</span></div>
          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="upload-form">
            <el-form-item label="源文件" required class="file-field">
              <el-upload ref="uploadRef" drag action="#" :auto-upload="false" :limit="1" :show-file-list="false" accept=".pdf,.docx,.md,.txt" @change="handleFileChange" @exceed="handleFileExceed">
                <div class="upload-content"><div class="upload-icon"><CloudUpload :size="24" /></div><strong>点击选择或拖拽文件到此处</strong><span>支持 PDF / DOCX / MD / TXT</span></div>
              </el-upload>
              <div v-if="file" class="selected-file"><FileText :size="16" /><span>{{ file.name }}</span><button title="移除文件" @click="clearFile"><X :size="15" /></button></div>
            </el-form-item>
            <el-form-item label="文档标题" prop="title" required><el-input v-model="form.title" maxlength="255" show-word-limit placeholder="例如：RDS 主备切换 SOP" /></el-form-item>
            <el-form-item label="文档类型" prop="doc_type" required><el-select v-model="form.doc_type" placeholder="选择文档类型" class="full-width"><el-option v-for="item in docTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="产品线" prop="product_line" required><el-input v-model="form.product_line" maxlength="64" placeholder="例如 ECS / VPC / RDS" /></el-form-item>
            <el-form-item label="产品版本" prop="product_version" required><el-input v-model="form.product_version" maxlength="32" placeholder="例如 V3.2" /></el-form-item>
          </el-form>
          <div class="form-actions"><span>提交后将自动开始解析、切块与向量化</span><el-button type="primary" :loading="submitting" :disabled="!file" @click="submit"><Upload :size="16" />开始上传</el-button></div>
        </section>

        <section class="progress-panel panel">
          <div class="panel-heading progress-heading"><div><span class="section-index">02</span><div><h2>入库进度</h2><p>显示最近 20 篇文档<span v-if="activeCount"> · {{ activeCount }} 篇正在处理</span></p></div></div><div class="polling-status" :class="{ active: polling }"><RefreshCw :size="14" :class="{ spinning: polling }" />{{ polling ? '每 3 秒自动刷新' : '已全部完成' }}</div></div>
          <el-alert v-if="firstLoadError" title="暂时无法加载文档进度" type="error" show-icon :closable="false" class="load-error"><el-button text type="danger" @click="loadDocuments({ initial: true })">重新加载</el-button></el-alert>
          <div class="table-wrap" v-loading="loading">
            <el-table :data="documents" row-key="id" :expand-row-keys="expandedRowKeys" class="document-table">
              <el-table-column prop="title" label="文档标题" min-width="250"><template #default="{ row }"><div class="title-cell"><span>{{ row.title }}</span><small v-if="row.version > 1">v{{ row.version }}</small></div></template></el-table-column>
              <el-table-column label="类型" width="120"><template #default="{ row }">{{ typeLabels[row.doc_type] || row.doc_type }}</template></el-table-column>
              <el-table-column prop="product_line" label="产品线" width="110" /><el-table-column prop="product_version" label="版本" width="110" />
              <el-table-column label="状态" min-width="150"><template #default="{ row }"><div class="status-cell"><el-tag :type="statusType(row.status)" effect="dark">{{ statusLabel(row.status) }}</el-tag><el-progress v-if="row.status === 'parsing'" :percentage="50" :indeterminate="true" :show-text="false" class="ingest-progress" /></div></template></el-table-column>
              <el-table-column label="chunk 数" width="100"><template #default="{ row }">{{ row.status === 'success' ? row.chunk_count : '-' }}</template></el-table-column><el-table-column label="上传时间" width="160"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
              <el-table-column type="expand" width="48"><template #default="{ row }"><el-alert v-if="row.status === 'failed'" :title="expandedReasons[row.id] || '入库失败，请重试'" type="error" :closable="false" show-icon description="请确认文件内容可解析，并检查文档格式后重新上传。" /></template></el-table-column>
              <template #empty><el-empty :image-size="72" description="还没有上传过文档，从上方表单开始" /></template>
            </el-table>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.document-page { min-height: 100vh; color: #dce8e8; background: #0d171d; background-image: linear-gradient(rgba(45,212,191,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.025) 1px,transparent 1px); background-size: 42px 42px; padding: 36px 42px 64px; }.page-grid{max-width:1360px;margin:0 auto}.page-header{display:flex;align-items:flex-start;gap:18px;margin-bottom:30px}.back-button{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.1);border-radius:10px;color:#90a9aa;background:rgba(255,255,255,.035);cursor:pointer;transition:.2s}.back-button:hover{color:#5eead4;border-color:rgba(45,212,191,.45);transform:translateX(-2px)}.eyebrow{color:#36b7aa;font:500 11px 'DM Mono',monospace;letter-spacing:1.7px;margin:1px 0 9px}h1,h2,p{margin:0}h1{font:600 28px 'Noto Serif SC',serif;letter-spacing:.5px;color:#f0f7f5}.page-header p{color:#789092;font-size:13px;margin-top:7px}.admin-chip{margin-left:auto;display:flex;align-items:center;gap:10px;padding:7px 12px 7px 7px;border:1px solid rgba(255,255,255,.09);background:rgba(255,255,255,.035);border-radius:10px;color:#d9e7e4;font-size:13px}.admin-chip small{display:block;color:#748c8e;font-size:10px;margin-bottom:2px}.admin-avatar{width:30px;height:30px;display:grid;place-items:center;border-radius:8px;background:#177f78;color:#d5fffa;font-weight:700}.panel{border:1px solid rgba(143,190,185,.13);background:rgba(16,30,36,.88);box-shadow:0 20px 55px rgba(0,0,0,.14);border-radius:12px;padding:24px 26px;margin-bottom:22px}.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}.panel-heading>div:first-child{display:flex;gap:13px}.section-index{color:#35b8a8;font:500 12px 'DM Mono',monospace;padding-top:3px}h2{font:600 17px 'Noto Serif SC',serif;color:#edf7f3}.panel-heading p{color:#708789;font-size:12px;margin-top:5px}.required-note{color:#789092;font-size:11px}.required-note i{display:inline-block;width:5px;height:5px;border-radius:50%;background:#f3a35b;margin:0 4px 1px 0}.upload-form{display:grid;grid-template-columns:minmax(260px,1.7fr) repeat(4,minmax(150px,1fr));gap:0 18px;align-items:start}.file-field{grid-row:span 2}.full-width{width:100%}.upload-form :deep(.el-form-item__label){color:#91a8a7;font-size:12px;padding-bottom:7px;line-height:1}.upload-form :deep(.el-input__wrapper),.upload-form :deep(.el-select__wrapper){background:rgba(5,14,18,.55);box-shadow:0 0 0 1px rgba(140,183,179,.16) inset;border-radius:7px;min-height:38px}.upload-form :deep(.el-input__inner),.upload-form :deep(.el-select__selected-item){color:#dce8e5}.upload-form :deep(.el-input__inner::placeholder){color:#536b6d}.file-field :deep(.el-upload),.file-field :deep(.el-upload-dragger){width:100%}.file-field :deep(.el-upload-dragger){height:124px;border:1px dashed rgba(45,212,191,.35);background:rgba(45,212,191,.035);border-radius:8px;padding:18px;transition:.2s}.file-field :deep(.el-upload-dragger:hover){border-color:#2dd4bf;background:rgba(45,212,191,.07)}.upload-content{display:flex;flex-direction:column;align-items:center;gap:6px}.upload-content strong{color:#cee2df;font-size:12px;font-weight:500}.upload-content span{color:#668083;font-size:11px}.upload-icon{display:grid;place-items:center;color:#3ed0be;margin-bottom:1px}.selected-file{display:flex;align-items:center;gap:7px;height:31px;padding:0 9px;margin-top:7px;color:#a6d5cf;background:rgba(45,212,191,.07);border:1px solid rgba(45,212,191,.15);border-radius:6px;font-size:11px}.selected-file span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}.selected-file button{border:0;background:transparent;color:#71918f;display:grid;place-items:center;cursor:pointer}.selected-file button:hover{color:#ff8e83}.form-actions{display:flex;justify-content:flex-end;align-items:center;gap:20px;border-top:1px solid rgba(255,255,255,.07);padding-top:18px}.form-actions span{color:#5e7778;font-size:11px}.form-actions :deep(.el-button--primary){border:none;background:#1e9e91;min-height:36px;border-radius:7px;padding:0 17px}.form-actions :deep(.el-button--primary:hover){background:#28b8a9}.form-actions :deep(.el-button .lucide){margin-right:7px;vertical-align:-3px}.progress-heading{margin-bottom:20px}.polling-status{display:flex;align-items:center;gap:6px;color:#657c7d;font-size:11px;padding-top:3px}.polling-status.active{color:#45cabc}.spinning{animation:spin 1.2s linear infinite}.load-error{margin-bottom:16px;background:rgba(185,59,60,.12);border:1px solid rgba(255,107,100,.2)}.table-wrap{overflow-x:auto}.document-table{--el-table-bg-color:transparent;--el-table-tr-bg-color:transparent;--el-table-header-bg-color:rgba(255,255,255,.035);--el-table-row-hover-bg-color:rgba(45,212,191,.045);--el-table-border-color:rgba(255,255,255,.07);--el-table-text-color:#b6c9c7;--el-table-header-text-color:#71898a;border-radius:8px;overflow:hidden}.document-table :deep(.el-table__header th){font-size:11px;font-weight:500;height:42px}.document-table :deep(.el-table__row td){height:56px;font-size:12px}.title-cell{display:flex;align-items:center;gap:8px;color:#d8e7e4;font-weight:500}.title-cell small{color:#40bbae;font:10px 'DM Mono',monospace}.status-cell{display:flex;align-items:center;gap:8px}.status-cell :deep(.el-tag){min-width:52px;justify-content:center;border:0}.status-cell :deep(.el-tag--info){color:#91a6a7;background:rgba(145,166,167,.12)}.status-cell :deep(.el-tag--success){background:rgba(45,190,143,.13);color:#50d8ae}.status-cell :deep(.el-tag--danger){background:rgba(245,104,94,.13);color:#ff8e83}.status-cell :deep(.el-tag:not(.el-tag--info):not(.el-tag--success):not(.el-tag--danger)){background:rgba(45,150,212,.13);color:#61bff0}.ingest-progress{width:56px}.document-table :deep(.el-progress-bar__outer){background:rgba(45,212,191,.1)}.document-table :deep(.el-progress-bar__inner){background:#38bcae}.document-table :deep(.el-table__expanded-cell){padding:10px 50px;background:rgba(245,104,94,.035)}.document-table :deep(.el-alert){background:transparent;padding:5px 0}.document-table :deep(.el-alert__title){color:#ff9b91;font-size:12px}.permission-result{padding:70px 0 100px;background:rgba(16,30,36,.8);border:1px solid rgba(255,255,255,.08);border-radius:12px}@keyframes spin{to{transform:rotate(360deg)}}@media (max-width:1000px){.document-page{padding:28px 20px 48px}.upload-form{grid-template-columns:repeat(2,minmax(180px,1fr))}.file-field{grid-row:auto;grid-column:1/-1}}@media (max-width:680px){.document-page{padding:20px 14px 36px}.page-header{gap:10px}h1{font-size:22px}.admin-chip{display:none}.panel{padding:18px 15px}.upload-form{display:block}.form-actions{align-items:stretch;flex-direction:column-reverse;gap:10px}.form-actions .el-button{width:100%}.progress-heading{gap:14px;flex-direction:column}.polling-status{padding-top:0}}
</style>
