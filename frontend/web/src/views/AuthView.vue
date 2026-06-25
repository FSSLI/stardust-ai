<template>
  <div class="min-h-screen bg-slate-900 flex">
    <!-- 左侧品牌区 -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-800 to-slate-900 items-center justify-center p-12">
      <div class="text-center max-w-md">
        <div class="text-8xl mb-6">✨</div>
        <h1 class="text-4xl font-bold text-white mb-4">星尘 Stardust AI</h1>
        <p class="text-xl text-slate-300 mb-6">一个有温度、有记忆、有性格的 AI 伙伴</p>
        <div class="space-y-3 text-slate-400 text-sm">
          <p>💬 随时倾诉，永不孤单</p>
          <p>🧠 记住你的点点滴滴</p>
          <p>🎭 三种人格，随心切换</p>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex items-center justify-center p-6">
      <div class="w-full max-w-sm">
        <!-- Logo（小屏可见） -->
        <div class="lg:hidden text-center mb-8">
          <div class="text-6xl mb-2">✨</div>
          <h1 class="text-2xl font-bold text-white">星尘 Stardust AI</h1>
        </div>

        <!-- Tab 切换 -->
        <div class="flex mb-6 bg-slate-800 rounded-xl p-1">
          <button
            @click="mode = 'login'"
            :class="[
              'flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors',
              mode === 'login' ? 'bg-stardust-600 text-white' : 'text-slate-400 hover:text-white'
            ]"
          >登录</button>
          <button
            @click="mode = 'register'"
            :class="[
              'flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors',
              mode === 'register' ? 'bg-stardust-600 text-white' : 'text-slate-400 hover:text-white'
            ]"
          >注册</button>
        </div>

        <!-- 表单 -->
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              placeholder="your@email.com"
              class="w-full bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500 transition-colors"
              required
              autocomplete="email"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1.5">密码</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="至少 6 位"
              class="w-full bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500 transition-colors"
              required
              minlength="6"
              autocomplete="current-password"
            />
          </div>

          <!-- 注册时的确认密码 -->
          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-slate-300 mb-1.5">确认密码</label>
            <input
              v-model="form.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              class="w-full bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500 transition-colors"
              required
              minlength="6"
              autocomplete="new-password"
            />
          </div>

          <!-- 注册时的验证码 -->
          <div v-if="mode === 'register'">
            <label class="block text-sm font-medium text-slate-300 mb-1.5">邮箱验证码</label>
            <div class="flex gap-2">
              <input
                v-model="form.code"
                type="text"
                maxlength="6"
                inputmode="numeric"
                placeholder="6 位数字"
                class="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500 transition-colors tracking-[4px] text-center text-lg"
                required
              />
              <button
                type="button"
                @click="handleSendCode"
                :disabled="codeCooldown > 0 || !form.email"
                class="px-4 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-sm text-slate-300 rounded-xl transition-colors whitespace-nowrap"
              >
                {{ codeCooldown > 0 ? codeCooldown + 's' : '发送验证码' }}
              </button>
            </div>
            <!-- 收不到提示 -->
            <p v-if="codeCooldown > 5" class="text-xs text-slate-500 mt-1.5">
              没收到？检查垃圾邮件，或等倒计时结束后重新发送
            </p>
            <p v-if="codeSent && codeCooldown === 0" class="text-xs text-amber-400 mt-1.5">
              仍未收到？
              <button type="button" @click="handleSendCode" class="underline hover:text-amber-300">重新发送</button>
            </p>
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMsg" class="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">
            {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="authStore.isLoading"
            class="w-full py-3 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-colors"
          >
            {{ authStore.isLoading ? '处理中...' : mode === 'login' ? '登录' : '创建账号' }}
          </button>
        </form>

        <!-- 分割线 -->
        <div class="my-6 flex items-center gap-3">
          <div class="flex-1 h-px bg-slate-700"></div>
          <span class="text-xs text-slate-500">或</span>
          <div class="flex-1 h-px bg-slate-700"></div>
        </div>

        <!-- 匿名体验 -->
        <button
          @click="handleAnonymous"
          :disabled="authStore.isLoading"
          class="w-full py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-300 rounded-xl font-medium transition-colors"
        >
          跳过，先体验 ✨
        </button>
        <p class="text-xs text-slate-500 text-center mt-3">无需注册，立即开始对话</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const errorMsg = ref('')
const codeCooldown = ref(0)
const codeSent = ref(false)

const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  code: ''
})

let cooldownTimer: ReturnType<typeof setInterval> | null = null

async function handleSendCode() {
  errorMsg.value = ''
  if (!form.email || codeCooldown.value > 0) return

  try {
    await axios.post('/api/v1/auth/send-code', { email: form.email })
    errorMsg.value = ''
    codeSent.value = true
    // 启动倒计时
    codeCooldown.value = 60
    cooldownTimer = setInterval(() => {
      codeCooldown.value--
      if (codeCooldown.value <= 0 && cooldownTimer) {
        clearInterval(cooldownTimer)
        cooldownTimer = null
      }
    }, 1000)
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '发送失败'
  }
}

async function handleSubmit() {
  errorMsg.value = ''

  if (mode.value === 'register') {
    if (form.password !== form.confirmPassword) {
      errorMsg.value = '两次密码不一致'
      return
    }
    if (!form.code || form.code.length !== 6) {
      errorMsg.value = '请输入 6 位验证码'
      return
    }
    const err = await authStore.register(form.email, form.password, form.code)
    if (err) {
      errorMsg.value = err
      return
    }
  } else {
    const err = await authStore.login(form.email, form.password)
    if (err) {
      errorMsg.value = err
      return
    }
  }

  router.push('/')
}

async function handleAnonymous() {
  errorMsg.value = ''
  // 清除倒计时
  if (cooldownTimer) clearInterval(cooldownTimer)
  const success = await authStore.loginAnonymous()
  if (success) {
    router.push('/')
  } else {
    errorMsg.value = '匿名登录失败，请重试'
  }
}
</script>
