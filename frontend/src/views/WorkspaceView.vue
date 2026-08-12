<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Bell, ArrowUpRight, BookOpen, FileText, CircleCheck, Clock3 } from '@lucide/vue'

const activeNav = ref('总览')
const query = ref('')
const question = ref('')
const navItems = ['总览', '知识文档', '智能问答', '运维工具']
const documents = [
  { title: '生产环境变更操作规范', type: '流程规范', updated: '2 小时前', status: '已发布', accent: 'green' },
  { title: 'Kubernetes 集群故障排查手册', type: '故障手册', updated: '昨天', status: '已发布', accent: 'blue' },
  { title: '数据库慢查询应急预案', type: '应急预案', updated: '3 天前', status: '待审核', accent: 'orange' },
]

function submitQuestion() {
  if (!question.value.trim()) return ElMessage.info('请输入你的运维问题')
  ElMessage.success('问题已提交，问答接口接入后将返回实时答案')
  question.value = ''
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-mark"><span>星</span></div>
      <div class="brand-copy"><strong>星海</strong><small>运维知识库</small></div>
      <nav class="main-nav">
        <button v-for="item in navItems" :key="item" :class="['nav-item', { active: activeNav === item }]" @click="activeNav = item">
          <span class="nav-dot" />{{ item }}<ArrowUpRight v-if="item === '运维工具'" :size="14" />
        </button>
      </nav>
      <div class="sidebar-footer"><div class="status-dot" />系统运行正常<span class="version">v0.1</span></div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div><p class="eyebrow">OPERATIONS INTELLIGENCE / 2026</p><h1>{{ activeNav }}</h1></div>
        <div class="top-actions"><label class="search-box"><Search :size="17" /><input v-model="query" placeholder="搜索知识、文档或服务..." /></label><button class="icon-button" aria-label="通知"><Bell :size="18" /><i /></button><div class="avatar">值</div></div>
      </header>

      <section class="hero-row">
        <div><p class="eyebrow warm">KNOWLEDGE AT A GLANCE</p><h2>把每一次排障<br /><em>变成下一次的答案。</em></h2><p class="hero-note">集中沉淀团队经验，让关键时刻的判断更快、更有依据。</p></div>
        <div class="hero-stamp"><span>本周知识活跃度</span><strong>84<small>%</small></strong><div class="trend">↗ 12.4% <b>较上周</b></div></div>
      </section>

      <section class="ask-panel">
        <div class="ask-icon">✦</div><div class="ask-body"><span>AI 运维助手</span><h3>遇到问题？从这里开始。</h3><div class="ask-input"><input v-model="question" placeholder="例如：如何排查线上服务 502 错误？" @keyup.enter="submitQuestion" /><button @click="submitQuestion">开始提问 <ArrowUpRight :size="16" /></button></div><div class="suggestions"><span>试试：</span><button @click="question = '查看今日生产环境变更'">今日变更记录</button><button @click="question = '搜索 Redis 连接超时排查方法'">Redis 连接超时</button><button @click="question = '查询 Kubernetes 常用排障命令'">K8s 常用命令</button></div></div><div class="ask-orbit">✧</div>
      </section>

      <section class="metrics-grid"><div class="metric"><div class="metric-icon green"><BookOpen :size="18" /></div><span>知识文档</span><strong>1,286</strong><small>↗ 8.6% 本月新增</small></div><div class="metric"><div class="metric-icon blue"><FileText :size="18" /></div><span>本周更新</span><strong>42</strong><small>覆盖 6 个业务域</small></div><div class="metric"><div class="metric-icon orange"><CircleCheck :size="18" /></div><span>待处理事项</span><strong>07</strong><small>需要你的关注</small></div><div class="metric"><div class="metric-icon purple"><Clock3 :size="18" /></div><span>平均响应</span><strong>1.8<span>min</span></strong><small>AI 辅助后提升 32%</small></div></section>

      <section class="content-section"><div class="section-heading"><div><p class="eyebrow">RECENT KNOWLEDGE</p><h3>最近更新</h3></div><button class="text-button">查看全部 <ArrowUpRight :size="15" /></button></div><div class="document-list"><article v-for="doc in documents" :key="doc.title" class="document-item"><div :class="['doc-icon', doc.accent]"><FileText :size="19" /></div><div class="doc-main"><h4>{{ doc.title }}</h4><p>{{ doc.type }} <span>·</span> 更新于 {{ doc.updated }}</p></div><span :class="['doc-status', doc.status === '待审核' ? 'pending' : 'published']">{{ doc.status }}</span><button class="row-arrow" aria-label="打开文档"><ArrowUpRight :size="17" /></button></article></div></section>

      <section class="bottom-grid"><div class="mini-section"><div class="section-heading"><div><p class="eyebrow">POPULAR TOPICS</p><h3>热门知识域</h3></div><button class="text-button">管理 <ArrowUpRight :size="15" /></button></div><div class="topic-grid"><button><b>容器与编排</b><span>238 篇</span></button><button><b>数据库</b><span>194 篇</span></button><button><b>网络与安全</b><span>167 篇</span></button><button><b>监控与告警</b><span>121 篇</span></button></div></div><div class="activity-panel"><p class="eyebrow">TEAM ACTIVITY</p><h3>团队动态</h3><div class="activity"><div class="activity-avatar">林</div><p><b>林晓峰</b> 更新了 <strong>生产发布规范</strong><small>12 分钟前</small></p></div><div class="activity"><div class="activity-avatar coral">陈</div><p><b>陈嘉</b> 收藏了 <strong>Redis 故障手册</strong><small>46 分钟前</small></p></div></div></section>
    </main>
  </div>
</template>
