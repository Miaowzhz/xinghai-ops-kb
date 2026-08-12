<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')

function login() {
  if (!username.value || !password.value) return
  auth.setSession('demo-token', { name: username.value, role: '运维团队' })
  router.push('/workspace')
}
</script>

<template>
  <main class="login-page">
    <section class="login-art"><div class="brand-mark"><span>星</span></div><p class="eyebrow warm">OPERATIONS INTELLIGENCE / 2026</p><h1>让经验<br /><em>在关键时刻发光。</em></h1><p>星海运维智能知识库<br />连接每一次排障与下一次更好的决策。</p></section>
    <section class="login-form"><div><p class="eyebrow">WELCOME BACK</p><h2>登录知识库</h2><p class="form-note">使用团队账号继续工作</p><form @submit.prevent="login"><label>账号<input v-model="username" placeholder="请输入账号" autocomplete="username" /></label><label>密码<input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" /></label><button type="submit">进入工作台 <span>↗</span></button></form></div><small>星海运维平台 · 内部使用</small></section>
  </main>
</template>
