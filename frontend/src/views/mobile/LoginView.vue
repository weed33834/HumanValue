<template>
  <div class="m-login">
    <div class="m-login__hero">
      <div class="m-login__logo">
        <BrandLogo :show-text="false" :size="64" />
      </div>
      <h1 class="m-login__title">HumanValue</h1>
      <p class="m-login__sub">人才价值分析与评估平台</p>
    </div>

    <div class="m-login__body">
      <!-- 演示模式：一键进入 -->
      <template v-if="demoEnabled">
        <button class="m-demo-btn" @click="handleDemoLogin('boss')">
          <span class="m-demo-btn__icon">👔</span>
          <span class="m-demo-btn__text">
            <strong>演示模式 · 直接进入</strong>
            <small>以管理者视角体验全部功能</small>
          </span>
          <span class="m-demo-btn__arrow">→</span>
        </button>
        <div class="m-divider"><span>或账号登录</span></div>
      </template>

      <!-- 账号登录（JWT） -->
      <form class="m-login__form" @submit.prevent="handleJwtLogin">
        <label class="m-field">
          <span class="m-field__label">邮箱</span>
          <input
            v-model="email"
            class="m-input"
            type="email"
            inputmode="email"
            autocomplete="email"
            placeholder="请输入邮箱"
          />
        </label>
        <label class="m-field">
          <span class="m-field__label">密码</span>
          <input
            v-model="password"
            class="m-input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            @keyup.enter="handleJwtLogin"
          />
        </label>
        <p v-if="error" class="m-login__error">{{ error }}</p>
        <button class="m-btn" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <button class="m-link" @click="goDesktop">使用桌面端 →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/client'
import { isDemoAuthEnabled } from '@/utils/auth'
import BrandLogo from '@/components/BrandLogo.vue'

const router = useRouter()
const auth = useAuthStore()

const demoEnabled = computed(() => isDemoAuthEnabled())
const loading = ref(false)
const error = ref('')

const email = ref(import.meta.env.DEV ? 'boss@humanvalue.ai' : '')
const password = ref(import.meta.env.DEV ? 'humanvalue123' : '')

// 移动端首页映射（登录后落对应 /m 页面）
const mobileHome = {
  boss: '/m/boss',
  manager: '/m/manager',
  employee: '/m/employee',
  hr: '/m/hr',
  admin: '/m/admin',
}

function handleDemoLogin(role) {
  if (!demoEnabled.value) {
    error.value = '演示模式未启用'
    return
  }
  auth.loginDemo(role)
  router.push(mobileHome[role])
}

async function handleJwtLogin() {
  if (!email.value || !password.value) {
    error.value = '请输入邮箱和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await authApi.login({ email: email.value, password: password.value })
    auth.loginWithToken(res.access_token, {
      user_id: res.user_id,
      name: res.name,
      role: res.role,
    })
    router.push(mobileHome[res.role] || '/m/login')
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    loading.value = false
  }
}

function goDesktop() {
  router.push('/login?desktop=1')
}
</script>

<style scoped>
.m-login {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg, #0f172a 0%, #1e293b 55%, #1f2937 100%);
  color: #fff;
  padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
}
.m-login__hero {
  text-align: center;
  padding: 56px 24px 32px;
}
.m-login__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.m-login__title {
  font-size: 26px;
  font-weight: 800;
  margin: 0 0 8px;
}
.m-login__sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.m-login__body {
  flex: 1;
  background: var(--el-bg-color);
  border-radius: 24px 24px 0 0;
  padding: 24px 20px calc(24px + env(safe-area-inset-bottom));
  color: var(--el-text-color-primary);
}

.m-demo-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 16px 18px;
  border: 1px solid var(--el-color-primary);
  border-radius: var(--av-radius-lg);
  background: var(--el-color-primary-light-9);
  cursor: pointer;
  transition: all var(--av-transition-fast) var(--av-ease-smooth);
}
.m-demo-btn:active {
  transform: scale(0.98);
  background: var(--el-color-primary-light-8);
}
.m-demo-btn__icon {
  font-size: 28px;
  flex-shrink: 0;
}
.m-demo-btn__text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
}
.m-demo-btn__text strong {
  font-size: 15px;
  color: var(--el-text-color-primary);
}
.m-demo-btn__text small {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.m-demo-btn__arrow {
  font-size: 18px;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.m-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  margin: 20px 0;
}
.m-divider::before,
.m-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--el-border-color-lighter);
}

.m-field {
  display: block;
  margin-bottom: 16px;
}
.m-field__label {
  display: block;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.m-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border: 1px solid var(--el-border-color);
  border-radius: var(--av-radius-md);
  font-size: 16px;
  background: var(--el-bg-color-blank);
  color: var(--el-text-color-primary);
  box-sizing: border-box;
  transition: border-color var(--av-transition-fast);
}
.m-input:focus {
  outline: none;
  border-color: var(--el-color-primary);
}
.m-login__error {
  color: #ef4444;
  font-size: 13px;
  margin: 0 0 12px;
}
.m-link {
  display: block;
  width: 100%;
  margin-top: 16px;
  background: none;
  border: none;
  color: var(--el-color-primary);
  font-size: 14px;
  cursor: pointer;
}
</style>
