<template>
  <div class="flex h-screen bg-slate-900">
    <!-- 左侧边栏 -->
    <aside class="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
      <!-- 顶部 -->
      <div class="p-4 border-b border-slate-700">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center">
            <span class="text-white text-lg">✨</span>
          </div>
          <h1 class="text-lg font-bold text-white">星尘 AI</h1>
        </div>
        <button
          @click="openCreateModal"
          class="w-full py-2 px-4 bg-stardust-600 hover:bg-stardust-500 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>新建记录</span>
        </button>
      </div>

      <!-- 导航菜单 -->
      <div class="p-2">
        <router-link
          to="/"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors"
        >
          <span>💬</span>
          <span>对话</span>
        </router-link>
        <router-link
          to="/journal"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-stardust-700/50 text-white transition-colors"
        >
          <span>📔</span>
          <span>手帐</span>
        </router-link>
      </div>

      <!-- 统计 -->
      <div class="p-4 border-t border-slate-700 mt-auto">
        <div class="text-xs text-slate-500 mb-2">统计概览</div>
        <div v-if="journalStore.stats" class="space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-slate-400">总记录</span>
            <span class="text-white font-medium">{{ journalStore.stats.total_entries }}</span>
          </div>
          <div v-for="(count, type) in journalStore.stats.by_type" :key="type" class="flex justify-between text-sm">
            <span class="text-slate-400">{{ typeLabel(type) }}</span>
            <span class="text-slate-300">{{ count }}</span>
          </div>
        </div>
        <div v-else class="text-sm text-slate-500">加载中...</div>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 筛选栏 -->
      <div class="p-4 border-b border-slate-700 bg-slate-800/50">
        <div class="flex items-center gap-3 flex-wrap">
          <h2 class="text-lg font-bold text-white mr-2">📔 手帐</h2>

          <!-- 类型筛选 -->
          <select
            v-model="journalStore.filters.entry_type"
            @change="onFilterChange"
            class="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-stardust-500"
          >
            <option value="">全部类型</option>
            <option value="note">📝 笔记</option>
            <option value="todo">✅ 待办</option>
            <option value="mood">💭 心情</option>
            <option value="memory">💾 回忆</option>
          </select>

          <!-- 日期筛选 -->
          <input
            v-model="journalStore.filters.date_from"
            @change="onFilterChange"
            type="date"
            class="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-stardust-500"
            title="开始日期"
          />
          <span class="text-slate-500 text-sm">至</span>
          <input
            v-model="journalStore.filters.date_to"
            @change="onFilterChange"
            type="date"
            class="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-stardust-500"
            title="结束日期"
          />

          <!-- 标签搜索 -->
          <input
            v-model="journalStore.filters.tag"
            @keydown.enter="onFilterChange"
            placeholder="搜索标签..."
            class="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 w-32 focus:outline-none focus:border-stardust-500"
          />

          <button
            v-if="hasFilters"
            @click="clearFilters"
            class="text-sm text-slate-400 hover:text-white transition-colors"
          >
            清除筛选
          </button>
        </div>

        <!-- 心情趋势 -->
        <div v-if="journalStore.stats?.mood_trend?.length" class="mt-3 flex items-center gap-2">
          <span class="text-xs text-slate-500">近7天心情：</span>
          <div class="flex items-center gap-1">
            <span
              v-for="(item, i) in journalStore.stats.mood_trend"
              :key="i"
              class="text-xs bg-slate-700 px-2 py-1 rounded"
              :title="item.date + ': ' + item.avg_mood + '分'"
            >
              {{ moodEmoji(Math.round(item.avg_mood)) }} {{ item.avg_mood }}
            </span>
          </div>
        </div>
      </div>

      <!-- 记录列表 -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- 加载中 -->
        <div v-if="journalStore.isLoading && journalStore.entries.length === 0" class="text-center py-20 text-slate-400">
          加载中...
        </div>

        <!-- 空状态 -->
        <div v-else-if="journalStore.entries.length === 0" class="text-center py-20">
          <div class="text-6xl mb-4">📔</div>
          <h3 class="text-xl font-bold text-white mb-2">还没有手帐记录</h3>
          <p class="text-slate-400 mb-6">记录你的心情、待办事项或美好回忆</p>
          <button
            @click="openCreateModal"
            class="px-6 py-3 bg-stardust-600 hover:bg-stardust-500 text-white rounded-xl transition-colors"
          >
            创建第一条记录
          </button>
        </div>

        <!-- 记录卡片列表 -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 max-w-6xl mx-auto">
          <div
            v-for="entry in journalStore.entries"
            :key="entry.id"
            class="bg-slate-800 border border-slate-700 rounded-xl p-4 hover:border-slate-600 transition-colors group"
          >
            <!-- 卡片头部 -->
            <div class="flex items-start justify-between mb-3">
              <span :class="[
                'px-2 py-0.5 rounded-full text-xs font-medium',
                entryTypeClass(entry.entry_type)
              ]">
                {{ entryTypeEmoji(entry.entry_type) }} {{ typeLabel(entry.entry_type) }}
              </span>
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  @click="openEditModal(entry)"
                  class="text-slate-400 hover:text-white p-1 text-xs"
                  title="编辑"
                >✏️</button>
                <button
                  @click="handleDelete(entry.id)"
                  class="text-slate-400 hover:text-red-400 p-1 text-xs"
                  title="删除"
                >🗑️</button>
              </div>
            </div>

            <!-- 内容 -->
            <p class="text-slate-200 whitespace-pre-wrap leading-relaxed mb-3">{{ entry.content }}</p>

            <!-- 心情分 -->
            <div v-if="entry.mood_score" class="mb-3 flex items-center gap-1">
              <span class="text-sm">{{ moodEmoji(entry.mood_score) }}</span>
              <span class="text-xs text-slate-400">{{ entry.mood_score }} / 10</span>
            </div>

            <!-- 底部信息 -->
            <div class="flex items-center justify-between text-xs text-slate-500">
              <div v-if="entry.tags" class="flex gap-1 flex-wrap">
                <span
                  v-for="tag in parseTagsDisplay(entry.tags)"
                  :key="tag"
                  class="bg-slate-700 px-2 py-0.5 rounded-full cursor-pointer hover:bg-slate-600 transition-colors"
                  @click="filterByTag(tag)"
                >#{{ tag }}</span>
              </div>
              <span class="ml-auto">{{ formatDate(entry.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="journalStore.total > journalStore.filters.page_size" class="flex justify-center mt-6 gap-2">
          <button
            @click="prevPage"
            :disabled="journalStore.filters.page <= 1"
            class="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          <span class="px-4 py-2 text-sm text-slate-400">
            {{ journalStore.filters.page }} / {{ totalPages }}
          </span>
          <button
            @click="nextPage"
            :disabled="journalStore.filters.page >= totalPages"
            class="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      </div>
    </main>

    <!-- 创建/编辑弹窗 -->
    <JournalEntryModal
      :show="showModal"
      :edit-entry="editingEntry"
      @close="closeModal"
      @saved="onSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useJournalStore, type JournalEntry } from '@/stores/journal'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import JournalEntryModal from '@/components/JournalEntryModal.vue'

const router = useRouter()
const journalStore = useJournalStore()
const chatStore = useChatStore()
const authStore = useAuthStore()

const showModal = ref(false)
const editingEntry = ref<JournalEntry | null>(null)

const totalPages = computed(() =>
  Math.ceil(journalStore.total / journalStore.filters.page_size)
)

const hasFilters = computed(() =>
  !!journalStore.filters.entry_type ||
  !!journalStore.filters.date_from ||
  !!journalStore.filters.date_to ||
  !!journalStore.filters.tag
)

onMounted(async () => {
  // 检查认证
  if (authStore.token) {
    const valid = await authStore.checkAuth()
    if (!valid) {
      router.push('/auth')
      return
    }
  } else if (!authStore.isAuthenticated) {
    router.push('/auth')
    return
  }

  // 同步匿名用户的 sessionId
  if (authStore.isAnonymous && authStore.user?.session_id) {
    chatStore.sessionId = authStore.user.session_id
  }
  if (!chatStore.sessionId) {
    await chatStore.initSession()
  }
  await loadData()
})

async function loadData() {
  await Promise.all([
    journalStore.fetchEntries(),
    journalStore.fetchStats()
  ])
}

function onFilterChange() {
  journalStore.filters.page = 1
  journalStore.fetchEntries()
}

function clearFilters() {
  journalStore.resetFilters()
  journalStore.fetchEntries()
}

function prevPage() {
  if (journalStore.filters.page > 1) {
    journalStore.filters.page--
    journalStore.fetchEntries()
  }
}

function nextPage() {
  if (journalStore.filters.page < totalPages.value) {
    journalStore.filters.page++
    journalStore.fetchEntries()
  }
}

function filterByTag(tag: string) {
  journalStore.filters.tag = tag
  journalStore.filters.page = 1
  journalStore.fetchEntries()
}

function openCreateModal() {
  editingEntry.value = null
  showModal.value = true
}

function openEditModal(entry: JournalEntry) {
  editingEntry.value = { ...entry }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingEntry.value = null
}

function onSaved() {
  loadData()
}

async function handleDelete(id: number) {
  if (!confirm('确定要删除这条记录吗？')) return
  const success = await journalStore.deleteEntry(id)
  if (success) {
    await loadData()
  }
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    note: '笔记',
    todo: '待办',
    mood: '心情',
    memory: '回忆'
  }
  return map[type] || type
}

function entryTypeEmoji(type: string): string {
  const map: Record<string, string> = {
    note: '📝',
    todo: '✅',
    mood: '💭',
    memory: '💾'
  }
  return map[type] || '📝'
}

function entryTypeClass(type: string): string {
  const map: Record<string, string> = {
    note: 'bg-blue-900/40 text-blue-300',
    todo: 'bg-green-900/40 text-green-300',
    mood: 'bg-purple-900/40 text-purple-300',
    memory: 'bg-amber-900/40 text-amber-300'
  }
  return map[type] || 'bg-slate-700 text-slate-300'
}

function moodEmoji(score: number): string {
  if (score <= 2) return '😞'
  if (score <= 4) return '😕'
  if (score <= 6) return '😐'
  if (score <= 8) return '🙂'
  return '😊'
}

function parseTagsDisplay(tags: string): string[] {
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
