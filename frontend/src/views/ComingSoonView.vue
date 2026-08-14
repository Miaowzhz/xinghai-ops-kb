<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ClipboardCheck, History } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const isHistory = computed(() => route.path === '/qa/history')
</script>

<template>
  <main class="placeholder-page">
    <header class="page-heading">
      <button class="back-button" title="返回智能问答" @click="router.push('/qa')"><ArrowLeft :size="18" /></button>
      <div><h1>{{ isHistory ? '问答历史记录' : '反馈审核工作台' }}</h1><p>{{ isHistory ? '集中检索和回看历史问答会话。' : '处理问答反馈并推动知识库持续改进。' }}</p></div>
    </header>
    <section class="placeholder-panel">
      <component :is="isHistory ? History : ClipboardCheck" :size="34" />
      <h2>{{ isHistory ? '历史记录功能正在建设' : '反馈审核功能正在建设' }}</h2>
      <p>当前入口和整体布局已经接通，后续业务页面将在这里直接承载。</p>
      <el-button type="primary" @click="router.push('/qa')">返回智能问答</el-button>
    </section>
  </main>
</template>

<style scoped>
.placeholder-page{max-width:1180px;margin:0 auto;padding:38px 42px}.page-heading{display:flex;align-items:flex-start;gap:18px;margin-bottom:28px}.page-heading h1{margin:0;color:#edf7f4;font:600 28px 'Noto Serif SC',serif}.page-heading p{margin:7px 0 0;color:#738a8b;font-size:13px}.back-button{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.1);border-radius:9px;color:#90a9aa;background:rgba(255,255,255,.035);cursor:pointer}.back-button:hover{color:#5eead4;border-color:rgba(45,212,191,.45)}.placeholder-panel{min-height:360px;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid rgba(143,190,185,.13);border-radius:10px;background:rgba(16,30,36,.88);color:#43c3b5;text-align:center}.placeholder-panel h2{margin:18px 0 7px;color:#dbeae7;font:600 17px 'Noto Serif SC',serif}.placeholder-panel p{margin:0 0 20px;color:#6f8687;font-size:12px}.placeholder-panel :deep(.el-button--primary){border:0;background:#1e9e91}@media(max-width:760px){.placeholder-page{padding:24px 16px}.page-heading h1{font-size:23px}}
</style>
