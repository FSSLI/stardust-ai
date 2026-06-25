<template>
  <div class="border-t border-slate-700">
    <button
      @click="expanded = !expanded"
      class="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/50 transition-colors"
    >
      <span class="text-sm text-slate-400 flex items-center gap-2">
        <span>🧠</span>
        <span>AI 记忆</span>
        <span v-if="hasMemory" class="w-1.5 h-1.5 rounded-full bg-green-400"></span>
      </span>
      <span class="text-slate-500 text-xs transition-transform" :class="expanded ? 'rotate-180' : ''">▼</span>
    </button>

    <div v-if="expanded" class="px-4 pb-4 space-y-3">
      <!-- 加载中 -->
      <div v-if="loading" class="text-xs text-slate-500 text-center py-3">加载中...</div>

      <!-- 无记忆 -->
      <div v-if="!hasMemory && !loading" class="text-xs text-slate-500 text-center py-3">
        还没有关于你的记忆
        <br />多发几条消息后 AI 会开始记住你
      </div>

      <!-- 记忆内容 -->
      <div v-if="hasMemory" class="space-y-2">
        <div v-for="(item, key) in memoryItems" :key="key" class="bg-slate-700/50 rounded-lg p-2.5">
          <div class="text-[11px] text-stardust-400 mb-1 font-medium">{{ item.label }}</div>
          <div class="text-xs text-slate-300 leading-relaxed">{{ item.value }}</div>
        </div>
      </div>

      <!-- 刷新按钮始终可见 -->
      <button
        @click="refreshMemory"
        :disabled="refreshing"
        class="w-full text-xs text-slate-400 hover:text-white py-1.5 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
      >
        {{ refreshing ? '刷新中...' : hasMemory ? '🔄 刷新记忆' : '✨ 生成记忆' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const expanded = ref(false)
const loading = ref(false)
const refreshing = ref(false)
const memoryData = ref<any>(null)

const hasMemory = computed(() => memoryData.value?.has_memory)

interface MemoryItem {
  label: string
  value: string
}

const memoryItems = computed<MemoryItem[]>(() => {
  if (!memoryData.value?.content) return []
  try {
    const data = typeof memoryData.value.content === 'string'
      ? JSON.parse(memoryData.value.content)
      : memoryData.value.content

    const labels: Record<string, string> = {
      basic_info: '📋 基本信息',
      preferences: '💡 偏好习惯',
      recent_status: '💭 近期状态',
      plans: '📌 重要约定'
    }

    return Object.entries(data)
      .filter(([_, v]) => v && v !== '暂无' && v !== '无')
      .map(([k, v]) => ({ label: labels[k] || k, value: v as string }))
      .filter(item => item.value !== 'raw')
  } catch {
    return []
  }
})

function getHeaders() {
  const headers: Record<string, string> = {}
  if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`
  const sid = localStorage.getItem('stardust_session_id')
  if (sid) headers['X-Session-Id'] = sid
  return headers
}

async function fetchMemory() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/memory', { headers: getHeaders() })
    memoryData.value = res.data.data
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

async function refreshMemory() {
  refreshing.value = true
  try {
    await axios.post('/api/v1/memory/summarize', {}, { headers: getHeaders() })
    await fetchMemory()
  } catch (e: any) {
    const msg = e.response?.data?.detail || '生成失败'
    // 简单提示后就消失，不影响使用
    alert(msg)
  } finally {
    refreshing.value = false
  }
}

watch(expanded, (val) => {
  if (val) fetchMemory()
})
</script>
