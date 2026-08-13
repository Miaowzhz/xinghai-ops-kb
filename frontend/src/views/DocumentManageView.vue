<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Eye, FilePenLine, RefreshCw, Search, Trash2, X } from '@lucide/vue'
import { useAuthStore } from '../stores/auth'
import { deleteDocument, getDocumentDetail, getDocumentList, reingestDocument } from '../api/document'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const uploadRef = ref()
const documents = ref([])
const total = ref(0)
const loading = ref(false)
const detailLoading = ref(false)
const reingestLoading = ref(false)
const deletingId = ref(null)
const listError = ref(false)
const drawerVisible = ref(false)
const dialogVisible = ref(false)
const detail = ref(null)
const selectedDocument = ref(null)
const newFile = ref(null)
const pollTimer = ref(null)
const polling = ref(false)
const page = ref(1)
const pageSize = ref(10)
const filters = reactive({ doc_type: '', product_line: '', status: '' })
const reingestForm = reactive({ product_version: '' })

const docTypes = [
  { value: 'manual', label: '产品手册' },
  { value: 'case', label: '故障案例' },
  { value: 'sop', label: '运维 SOP' },
  { value: 'api', label: 'API 文档' },
]
const typeLabels = Object.fromEntries(docTypes.map(item => [item.value, item.label]))
const statusOptions = [
  { value: 'pending', label: '待入库' },
  { value: 'parsing', label: '入库中' },
  { value: 'success', label: '成功' },
  { value: 'failed', label: '失败' },
]
const productLines = ['ECS', 'VPC', 'RDS', 'OSS']
const activeDocuments = computed(() => documents.value.some(item => ['pending', 'parsing'].includes(item.status)))
const isEmptyFiltered = computed(() => !loading.value && !listError.value && total.value === 0 && Object.values(filters).some(Boolean))
const reingestRules = {
  product_version: [{ required: true, message: '请输入新版本号', trigger: 'blur' }, { min: 1, max: 32, message: '版本号长度为 1-32 个字符', trigger: 'blur' }],
}

function formatTime(value, withSeconds = false) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = number => String(number).padStart(2, '0')
  const base = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
  return withSeconds ? `${base}:${pad(date.getSeconds())}` : base
}
function statusLabel(value) { return { pending: '待入库', parsing: '入库中', success: '成功', failed: '失败' }[value] || value }
function statusType(value) { return { pending: 'info', parsing: 'warning', success: 'success', failed: 'danger' }[value] || 'info' }
function isAllowed(fileItem) { return ['pdf', 'docx', 'md', 'txt'].includes(fileItem.name.split('.').pop()?.toLowerCase()) }
function errorDetail(error, fallback) { return error.response?.data?.detail || fallback }

async function loadDocuments({ silent = false } = {}) {
  if (!silent) loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    Object.entries(filters).forEach(([key, value]) => { if (value) params[key] = value })
    const response = await getDocumentList(params)
    documents.value = response.items || []
    total.value = response.total || 0
    listError.value = false
    if (activeDocuments.value) startPolling()
    else stopPolling()
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error('仅知识管理员可执行此操作')
      router.push('/workspace')
      return
    }
    listError.value = true
    if (!silent) ElMessage.error('文档列表加载失败')
    else ElMessage.warning('进度刷新失败，将在 3 秒后重试')
    console.error('加载文档列表失败', error)
  } finally { loading.value = false }
}
function startPolling() {
  if (pollTimer.value) return
  polling.value = true
  pollTimer.value = window.setInterval(() => loadDocuments({ silent: true }), 3000)
}
function stopPolling() {
  if (pollTimer.value) window.clearInterval(pollTimer.value)
  pollTimer.value = null
  polling.value = false
}
function query() { page.value = 1; loadDocuments() }
function resetFilters() { filters.doc_type = ''; filters.product_line = ''; filters.status = ''; page.value = 1; loadDocuments() }
function handlePageChange(value) { page.value = value; loadDocuments() }
function handleSizeChange(value) { pageSize.value = value; page.value = 1; loadDocuments() }

async function openDetail(row) {
  detailLoading.value = true
  try {
    detail.value = await getDocumentDetail(row.id)
    drawerVisible.value = true
  } catch (error) {
    if (error.response?.status === 403) ElMessage.error('仅知识管理员可执行此操作')
    else ElMessage.error('详情加载失败')
  } finally { detailLoading.value = false }
}
function openReingest(row) {
  selectedDocument.value = row
  reingestForm.product_version = row.product_version
  newFile.value = null
  uploadRef.value?.clearFiles()
  formRef.value?.clearValidate()
  dialogVisible.value = true
}
function handleFileChange(uploadFile) {
  if (!isAllowed(uploadFile)) {
    ElMessage.warning('仅支持 PDF / DOCX / MD / TXT 格式')
    clearNewFile()
    return
  }
  newFile.value = uploadFile.raw
}
function clearNewFile() { newFile.value = null; uploadRef.value?.clearFiles() }
async function submitReingest() {
  if (!newFile.value) { ElMessage.warning('请选择新版文档文件'); return }
  await formRef.value.validate(async valid => {
    if (!valid) return
    reingestLoading.value = true
    const data = new FormData()
    data.append('file', newFile.value)
    data.append('product_version', reingestForm.product_version.trim())
    try {
      await reingestDocument(selectedDocument.value.id, data)
      dialogVisible.value = false
      ElMessage.success('已提交，正在重新入库')
      await loadDocuments()
    } catch (error) {
      if (error.response?.status === 403) ElMessage.error('仅知识管理员可执行此操作')
      else if (error.response?.status === 409) ElMessage.error('文档正在入库中，请稍后再操作')
      else if (error.response?.status === 400) ElMessage.error('仅支持 PDF / DOCX / MD / TXT 格式')
      else ElMessage.error('提交失败，请重试')
    } finally { reingestLoading.value = false }
  })
}
async function removeDocument(row) {
  if (row.status === 'parsing') return
  try {
    await ElMessageBox.confirm(`删除后不可恢复，将同时删除该文档在知识库中的全部 ${row.chunk_count || 0} 个分片，确认删除《${row.title}》吗？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning', distinguishCancelAndClose: true })
  } catch { return }
  deletingId.value = row.id
  try {
    await deleteDocument(row.id)
    ElMessage.success('删除成功')
    if (documents.value.length === 1 && page.value > 1) page.value -= 1
    await loadDocuments()
  } catch (error) {
    if (error.response?.status === 403) ElMessage.error('仅知识管理员可执行此操作')
    else if (error.response?.status === 409) ElMessage.error('文档正在入库中，请稍后再删除')
    else if (error.response?.status === 404) { ElMessage.error('文档不存在或已被删除'); await loadDocuments() }
    else ElMessage.error('删除失败，请重试')
  } finally { deletingId.value = null }
}
function logout() { auth.clearSession(); router.push('/login') }

onMounted(() => {
  if (!auth.isAdmin) { ElMessage.error('仅知识管理员可访问'); router.push('/workspace'); return }
  loadDocuments()
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="manage-page">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">星</span><span>星海运维智能知识库</span></div>
      <div class="topbar-user"><span>{{ auth.user?.display_name || '管理员' }}</span><el-tag type="success" effect="dark">admin</el-tag><button title="退出登录" @click="logout"><X :size="16" /></button></div>
    </header>
    <main class="manage-main">
      <div class="page-title-row"><div class="title-with-back"><button class="back-button" title="返回工作台" @click="router.push('/workspace')"><ArrowLeft :size="18" /></button><div><div class="eyebrow">KNOWLEDGE BASE / CATALOG</div><h1>知识库文档管理</h1><p>管理已入库资料的版本、状态与生命周期。</p></div></div><div class="polling" :class="{ active: polling }"><RefreshCw :size="14" :class="{ spinning: polling }" />{{ polling ? '正在同步入库状态' : '状态已同步' }}</div></div>

      <section class="filter-bar panel">
        <el-form inline class="filter-form" @submit.prevent="query">
          <el-form-item label="文档类型"><el-select v-model="filters.doc_type" placeholder="全部类型" clearable><el-option v-for="item in docTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
          <el-form-item label="产品线"><el-select v-model="filters.product_line" placeholder="全部产品线" clearable><el-option v-for="line in productLines" :key="line" :label="line" :value="line" /></el-select></el-form-item>
          <el-form-item label="状态"><el-select v-model="filters.status" placeholder="全部状态" clearable><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
          <el-form-item class="filter-actions"><el-button type="primary" @click="query"><Search :size="15" />查询</el-button><el-button @click="resetFilters">重置</el-button></el-form-item>
        </el-form>
      </section>

      <section class="table-panel panel">
        <div class="table-heading"><div><h2>文档账本</h2><span>共 {{ total }} 篇资料</span></div><span class="hint">文档内容变化请通过“重新上传新版”进入新一轮入库</span></div>
        <div v-loading="loading" class="table-wrap">
          <el-alert v-if="listError" title="文档列表加载失败" type="error" show-icon :closable="false" class="list-error"><el-button text type="danger" @click="loadDocuments()">重试</el-button></el-alert>
          <el-table v-else :data="documents" class="manage-table" row-key="id">
            <el-table-column label="标题" min-width="240"><template #default="{ row }"><el-tooltip :content="row.title" placement="top"><span class="ellipsis title-text">{{ row.title }}</span></el-tooltip></template></el-table-column>
            <el-table-column label="类型" width="120"><template #default="{ row }">{{ typeLabels[row.doc_type] || row.doc_type }}</template></el-table-column><el-table-column prop="product_line" label="产品线" width="100" />
            <el-table-column label="版本" width="150"><template #default="{ row }"><span>{{ row.product_version }}</span><small class="version-count">第 {{ row.version }} 次</small></template></el-table-column><el-table-column label="chunk 数" width="95"><template #default="{ row }">{{ row.chunk_count || 0 }}</template></el-table-column>
            <el-table-column label="状态" width="125"><template #default="{ row }"><el-tooltip v-if="row.status === 'failed'" :content="row.fail_reason || '入库失败，请重试'" placement="top"><el-tag :type="statusType(row.status)" effect="dark">{{ statusLabel(row.status) }}</el-tag></el-tooltip><el-tag v-else :type="statusType(row.status)" effect="dark">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
            <el-table-column prop="created_by_name" label="上传人" width="105" /><el-table-column label="上传时间" width="155"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
            <el-table-column label="操作" width="220" fixed="right"><template #default="{ row }"><div class="row-actions"><el-button link :loading="detailLoading && detail?.id === row.id" @click="openDetail(row)"><Eye :size="14" />详情</el-button><el-button link :disabled="row.status === 'parsing'" @click="openReingest(row)"><FilePenLine :size="14" />重新上传</el-button><el-tooltip v-if="row.status === 'parsing'" content="入库中，暂不可删除"><span><el-button link disabled><Trash2 :size="14" />删除</el-button></span></el-tooltip><el-button v-else link type="danger" :loading="deletingId === row.id" @click="removeDocument(row)"><Trash2 :size="14" />删除</el-button></div></template></el-table-column>
            <template #empty><el-empty :image-size="70" :description="isEmptyFiltered ? '没有符合条件的文档，试试调整筛选条件' : '暂无文档，请先到文档上传页上传资料'" /></template>
          </el-table>
        </div>
        <div class="pagination-row"><span>共 {{ total }} 条</span><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @current-change="handlePageChange" @size-change="handleSizeChange" /></div>
      </section>
    </main>

    <el-drawer v-model="drawerVisible" title="文档详情" size="440px" class="detail-drawer"><template v-if="detail"><div class="drawer-title"><h2>{{ detail.title }}</h2><el-tag :type="statusType(detail.status)" effect="dark">{{ statusLabel(detail.status) }}</el-tag></div><el-descriptions :column="1" border class="detail-descriptions"><el-descriptions-item label="文档类型">{{ typeLabels[detail.doc_type] || detail.doc_type }}</el-descriptions-item><el-descriptions-item label="产品线">{{ detail.product_line }}</el-descriptions-item><el-descriptions-item label="产品版本">{{ detail.product_version }}（第 {{ detail.version }} 次入库）</el-descriptions-item><el-descriptions-item label="文件类型">{{ (detail.file_type || '').toUpperCase() || '-' }}</el-descriptions-item><el-descriptions-item label="chunk 数">{{ detail.chunk_count || 0 }}</el-descriptions-item><el-descriptions-item label="上传人">{{ detail.created_by_name || '-' }}</el-descriptions-item><el-descriptions-item label="上传时间">{{ formatTime(detail.created_at, true) }}</el-descriptions-item><el-descriptions-item label="更新时间">{{ formatTime(detail.updated_at, true) }}</el-descriptions-item><el-descriptions-item label="失败原因">{{ detail.fail_reason || '-' }}</el-descriptions-item></el-descriptions></template></el-drawer>

    <el-dialog v-model="dialogVisible" title="重新上传新版文档" width="480px" :close-on-click-modal="false" class="reingest-dialog"><div class="current-doc">当前文档：<strong>{{ selectedDocument?.title }}</strong><span>{{ selectedDocument?.product_version }}</span></div><el-form ref="formRef" :model="reingestForm" :rules="reingestRules" label-position="top"><el-form-item label="新版本号" prop="product_version"><el-input v-model="reingestForm.product_version" maxlength="32" placeholder="例如 V3.3" /></el-form-item><el-form-item label="新版文档文件" required><el-upload ref="uploadRef" drag action="#" :auto-upload="false" :limit="1" :show-file-list="false" accept=".pdf,.docx,.md,.txt" @change="handleFileChange"><div class="dialog-upload"><FilePenLine :size="22" /><span>点击选择新版文件</span><small>支持 PDF / DOCX / MD / TXT</small></div></el-upload><div v-if="newFile" class="new-file">{{ newFile.name }}<button @click="clearNewFile"><X :size="14" /></button></div></el-form-item></el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="reingestLoading" @click="submitReingest">开始上传</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.back-button{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.1);border-radius:10px;color:#90a9aa;background:rgba(255,255,255,.035);cursor:pointer;transition:.2s}.back-button:hover{color:#5eead4;border-color:rgba(45,212,191,.45);transform:translateX(-2px)}.title-with-back{display:flex;align-items:flex-start;gap:18px}
.manage-page{min-height:100vh;color:#dce8e8;background:#0d171d;background-image:linear-gradient(rgba(45,212,191,.022) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.022) 1px,transparent 1px);background-size:42px 42px}.topbar{height:68px;display:flex;align-items:center;justify-content:space-between;padding:0 42px;border-bottom:1px solid rgba(255,255,255,.07);background:rgba(10,20,25,.78)}.brand{display:flex;align-items:center;gap:10px;color:#d9e9e5;font:600 15px 'Noto Serif SC',serif}.brand-mark{width:31px;height:31px;display:grid;place-items:center;border-radius:8px;background:#178d83;color:#e5fffa;font-weight:700}.topbar-user{display:flex;align-items:center;gap:10px;color:#a9bdbc;font-size:13px}.topbar-user :deep(.el-tag){border:0;background:rgba(45,190,143,.13);color:#55d5ae}.topbar-user button{display:grid;place-items:center;border:0;background:transparent;color:#718787;cursor:pointer;margin-left:7px}.topbar-user button:hover{color:#ff9187}.manage-main{max-width:1440px;margin:0 auto;padding:38px 42px 60px}.page-title-row{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:25px}.eyebrow{color:#35b8a8;font:500 11px 'DM Mono',monospace;letter-spacing:1.6px;margin-bottom:9px}.page-title-row h1{margin:0;color:#eef8f5;font:600 29px 'Noto Serif SC',serif}.page-title-row p{color:#738a8b;font-size:13px;margin-top:8px}.polling{display:flex;align-items:center;gap:6px;color:#687e80;font-size:11px}.polling.active{color:#48cbbd}.spinning{animation:spin 1.2s linear infinite}.panel{border:1px solid rgba(143,190,185,.13);background:rgba(16,30,36,.88);border-radius:11px;box-shadow:0 20px 50px rgba(0,0,0,.13)}.filter-bar{padding:19px 22px 5px;margin-bottom:18px}.filter-form :deep(.el-form-item){margin-right:18px;margin-bottom:14px}.filter-form :deep(.el-form-item__label){color:#7f9998;font-size:12px}.filter-form :deep(.el-select){width:155px}.filter-actions :deep(.el-button--primary){border:0;background:#1e9e91}.filter-actions :deep(.el-button .lucide){vertical-align:-3px;margin-right:5px}.table-panel{padding:22px 22px 16px}.table-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:17px}.table-heading h2{display:inline;color:#eaf5f2;font:600 17px 'Noto Serif SC',serif;margin:0 11px 0 0}.table-heading span{color:#668082;font-size:11px}.table-heading .hint{font-size:11px;color:#597375}.table-wrap{overflow-x:auto;min-height:285px}.manage-table{--el-table-bg-color:transparent;--el-table-tr-bg-color:transparent;--el-table-header-bg-color:rgba(255,255,255,.035);--el-table-row-hover-bg-color:rgba(45,212,191,.045);--el-table-border-color:rgba(255,255,255,.07);--el-table-text-color:#b9cbca;--el-table-header-text-color:#718889;border-radius:8px;overflow:hidden}.manage-table :deep(.el-table__header th){height:43px;font-size:11px;font-weight:500}.manage-table :deep(.el-table__row td){height:57px;font-size:12px}.ellipsis{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.title-text{color:#d8e8e4;font-weight:500}.version-count{display:block;color:#5f8884;font:10px 'DM Mono',monospace;margin-top:3px}.manage-table :deep(.el-tag){border:0;min-width:52px;justify-content:center}.manage-table :deep(.el-tag--warning){background:rgba(237,160,70,.13);color:#f5be73}.manage-table :deep(.el-tag--info){background:rgba(145,166,167,.12);color:#94a8a7}.manage-table :deep(.el-tag--success){background:rgba(45,190,143,.13);color:#55d5ae}.manage-table :deep(.el-tag--danger){background:rgba(245,104,94,.13);color:#ff9187}.row-actions{display:flex;align-items:center;gap:3px}.row-actions :deep(.el-button){padding:4px 5px;font-size:11px}.row-actions :deep(.el-button .lucide){vertical-align:-3px;margin-right:3px}.list-error{margin:25px}.pagination-row{display:flex;justify-content:space-between;align-items:center;padding:18px 3px 0;color:#6f8586;font-size:11px}.pagination-row :deep(.el-pagination){--el-pagination-bg-color:transparent;--el-pagination-text-color:#829998;--el-pagination-button-color:#829998;--el-pagination-hover-color:#42c9ba}.detail-drawer :deep(.el-drawer){background:#122127;color:#dce8e5}.drawer-title{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,.08);padding-bottom:17px;margin-bottom:18px}.drawer-title h2{font:600 18px 'Noto Serif SC',serif;color:#eaf6f2;margin:0;max-width:280px}.detail-descriptions{--el-descriptions-item-bordered-label-background:rgba(255,255,255,.035);--el-descriptions-item-bordered-content-background:transparent;--el-border-color-lighter:rgba(255,255,255,.08);--el-text-color-regular:#c6d7d4;--el-text-color-primary:#8ca3a2}.current-doc{color:#7e9797;background:rgba(45,212,191,.05);border:1px solid rgba(45,212,191,.13);border-radius:7px;padding:12px 13px;margin-bottom:20px;font-size:12px}.current-doc strong{color:#d9eeea}.current-doc span{color:#40bbae;margin-left:8px;font:11px 'DM Mono',monospace}.reingest-dialog :deep(.el-dialog){background:#122127;border:1px solid rgba(143,190,185,.16)}.reingest-dialog :deep(.el-dialog__title){color:#eaf5f2}.reingest-dialog :deep(.el-form-item__label){color:#8ba1a0;font-size:12px}.reingest-dialog :deep(.el-input__wrapper){background:rgba(5,14,18,.55);box-shadow:0 0 0 1px rgba(140,183,179,.16) inset}.reingest-dialog :deep(.el-input__inner){color:#e0edeb}.reingest-dialog :deep(.el-upload),.reingest-dialog :deep(.el-upload-dragger){width:100%}.reingest-dialog :deep(.el-upload-dragger){height:100px;padding:18px;background:rgba(45,212,191,.035);border:1px dashed rgba(45,212,191,.3);border-radius:7px}.dialog-upload{display:flex;align-items:center;justify-content:center;gap:9px;color:#9fc5c0;font-size:12px;flex-wrap:wrap}.dialog-upload svg{color:#38c6b7}.dialog-upload small{width:100%;color:#64807f;font-size:10px}.new-file{display:flex;justify-content:space-between;align-items:center;color:#9bd2cb;font-size:11px;margin-top:8px;padding:7px 9px;background:rgba(45,212,191,.06);border-radius:5px}.new-file button{display:grid;place-items:center;border:0;background:transparent;color:#769291;cursor:pointer}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:800px){.topbar{padding:0 18px}.brand{font-size:13px}.manage-main{padding:27px 16px 45px}.page-title-row{align-items:flex-start;gap:14px;flex-direction:column}.filter-form :deep(.el-form-item){margin-right:8px}.filter-form :deep(.el-select){width:145px}.table-heading .hint{display:none}.pagination-row{align-items:flex-start;gap:10px;flex-direction:column}.detail-drawer :deep(.el-drawer){width:90%!important}}@media(max-width:500px){.topbar-user span,.topbar-user :deep(.el-tag){display:none}.filter-bar{padding-left:13px;padding-right:13px}.filter-form :deep(.el-form-item){width:calc(50% - 8px)}.filter-form :deep(.el-form-item .el-select){width:100%}.filter-actions{width:100%!important}.filter-actions :deep(.el-button){flex:1}.page-title-row h1{font-size:24px}}
</style>
