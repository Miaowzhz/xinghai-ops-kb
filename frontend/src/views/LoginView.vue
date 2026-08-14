<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Eye, EyeOff, ArrowRight, Loader } from '@lucide/vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const focused = ref({ username: false, password: false })

const isFormValid = computed(() => username.value.trim().length > 0 && password.value.length > 0)

function onFocus(field) {
  focused.value[field] = true
}

function onBlur(field) {
  focused.value[field] = false
}

async function handleLogin() {
  if (!isFormValid.value) {
    if (!username.value.trim()) ElMessage.warning('请输入账号')
    else if (!password.value) ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    // 成功动画一小会再跳转
    setTimeout(() => {
      router.push('/qa')
    }, 600)
  } catch (error) {
    const detail = error.response?.data?.detail
    ElMessage.error(detail || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}

function togglePassword() {
  showPassword.value = !showPassword.value
}
</script>

<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card" :class="{ 'logging-in': loading }">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-mark">
          <span>星</span>
        </div>
        <div class="logo-pulse"></div>
      </div>

      <h1 class="title">星海运维</h1>
      <p class="subtitle">智能知识库</p>

      <!-- 表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <!-- 用户名 -->
        <div class="input-group" :class="{ focused: focused.username || username, hasValue: username }">
          <label>账号</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            :disabled="loading"
            @focus="onFocus('username')"
            @blur="onBlur('username')"
            @keyup.enter="handleLogin"
          />
          <div class="input-line"></div>
        </div>

        <!-- 密码 -->
        <div class="input-group" :class="{ focused: focused.password || password, hasValue: password }">
          <label>密码</label>
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            :disabled="loading"
            @focus="onFocus('password')"
            @blur="onBlur('password')"
            @keyup.enter="handleLogin"
          />
          <button type="button" class="toggle-password" @click="togglePassword" :disabled="loading">
            <Eye v-if="showPassword" :size="18" />
            <EyeOff v-else :size="18" />
          </button>
          <div class="input-line"></div>
        </div>

        <!-- 登录按钮 -->
        <button
          type="submit"
          class="login-btn"
          :class="{ active: isFormValid && !loading, loading: loading }"
          :disabled="loading"
        >
          <span v-if="!loading" class="btn-text">
            进入系统
            <ArrowRight :size="18" class="btn-arrow" />
          </span>
          <span v-else class="btn-loading">
            <Loader :size="20" class="spin" />
          </span>
          <div class="btn-glow"></div>
        </button>
      </form>

      <p class="footer-text">内部使用 · 请勿外传</p>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1923;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* 背景光晕 */
.bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: #2dd4bf;
  top: -10%;
  left: -5%;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #3b82f6;
  bottom: -10%;
  right: -5%;
  animation-delay: -7s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: #8b5cf6;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(20px, 30px) scale(1.02); }
}

/* 登录卡片 */
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 380px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-card.logging-in {
  transform: scale(0.98);
  opacity: 0.8;
}

/* Logo */
.logo-area {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 28px;
}

.logo-mark {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-family: 'Noto Serif SC', serif;
  font-size: 26px;
  font-weight: 700;
  color: white;
  position: relative;
  z-index: 2;
  animation: logoBreath 3s ease-in-out infinite;
}

@keyframes logoBreath {
  0%, 100% { box-shadow: 0 0 20px rgba(45, 212, 191, 0.3); }
  50% { box-shadow: 0 0 40px rgba(45, 212, 191, 0.5), 0 0 60px rgba(59, 130, 246, 0.2); }
}

.logo-pulse {
  position: absolute;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  animation: pulse 2s ease-out infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(1.8); opacity: 0; }
}

/* 标题 */
.title {
  text-align: center;
  font-family: 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 6px;
  letter-spacing: 2px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: rgba(148, 163, 184, 0.8);
  margin: 0 0 40px;
  letter-spacing: 4px;
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.input-group {
  position: relative;
}

.input-group label {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: rgba(148, 163, 184, 0.6);
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-group.focused label,
.input-group.hasValue label {
  top: -10px;
  font-size: 12px;
  color: #2dd4bf;
  letter-spacing: 1px;
}

.input-group input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  padding: 12px 36px 12px 0;
  font-size: 15px;
  color: #f1f5f9;
  outline: none;
  transition: all 0.3s ease;
}

.input-group input::placeholder {
  color: transparent;
}

.input-group input:disabled {
  opacity: 0.5;
}

.input-line {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #2dd4bf, #3b82f6);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-group.focused .input-line {
  width: 100%;
}

.toggle-password {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(148, 163, 184, 0.5);
  cursor: pointer;
  padding: 8px;
  margin: -8px;
  transition: color 0.2s ease;
}

.toggle-password:hover {
  color: #2dd4bf;
}

.toggle-password:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* 登录按钮 */
.login-btn {
  position: relative;
  width: 100%;
  height: 52px;
  margin-top: 12px;
  border: none;
  border-radius: 14px;
  background: rgba(148, 163, 184, 0.1);
  color: rgba(148, 163, 184, 0.4);
  font-size: 15px;
  font-weight: 500;
  cursor: not-allowed;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-btn.active {
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(45, 212, 191, 0.3);
}

.login-btn.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(45, 212, 191, 0.4);
}

.login-btn.active:hover .btn-arrow {
  transform: translateX(4px);
}

.login-btn.loading {
  background: linear-gradient(135deg, #2dd4bf, #3b82f6);
  cursor: wait;
}

.btn-arrow {
  transition: transform 0.3s ease;
}

.btn-text {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.login-btn.active:hover .btn-glow {
  opacity: 1;
}

/* 页脚 */
.footer-text {
  text-align: center;
  margin-top: 32px;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.3);
  letter-spacing: 2px;
}

/* 入场动画 */
.login-card {
  animation: cardIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) both;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo-area { animation: fadeUp 0.6s ease 0.1s both; }
.title { animation: fadeUp 0.6s ease 0.2s both; }
.subtitle { animation: fadeUp 0.6s ease 0.25s both; }
.input-group:nth-child(1) { animation: fadeUp 0.6s ease 0.3s both; }
.input-group:nth-child(2) { animation: fadeUp 0.6s ease 0.4s both; }
.login-btn { animation: fadeUp 0.6s ease 0.5s both; }
.footer-text { animation: fadeUp 0.6s ease 0.6s both; }

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
