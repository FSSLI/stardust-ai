<template>
  <div class="flex h-screen bg-slate-900">
    <!-- 左侧边栏 -->
    <aside class="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
      <!-- 顶部 -->
      <div class="p-4 border-b border-slate-700">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center">
            <span class="text-white text-lg">{{ currentPersonaEmoji }}</span>
          </div>
          <h1 class="text-lg font-bold text-white">星尘 AI</h1>
        </div>
        <button 
          @click="createNewChat"
          class="w-full py-2 px-4 bg-stardust-600 hover:bg-stardust-500 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>新建对话</span>
        </button>
      </div>

      <!-- 导航菜单 -->
      <div class="p-2">
        <router-link
          to="/"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-stardust-700/50 text-white transition-colors"
        >
          <span>💬</span>
          <span>对话</span>
        </router-link>
        <router-link
          to="/journal"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors"
        >
          <span>📔</span>
          <span>手帐</span>
        </router-link>
      </div>

      <!-- 搜索框 -->
      <div class="px-2 pt-2">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索对话..."
          class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500"
        />
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto p-2">
        <div v-if="filteredConversations.length === 0 && searchQuery" class="text-xs text-slate-500 text-center py-4">
          未找到匹配的对话
        </div>
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          @click="loadConversation(conv.id)"
          :class="[
            'p-3 rounded-lg cursor-pointer mb-1 transition-colors group relative',
            chatStore.currentConversationId === conv.id
              ? 'bg-stardust-700/50 border border-stardust-500/50'
              : 'hover:bg-slate-700'
          ]"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm">💬</span>
            <span class="text-sm text-slate-200 truncate flex-1">{{ conv.title || '新对话' }}</span>
          </div>
          <div class="text-xs text-slate-400 mt-1">
            {{ formatDate(conv.updated_at) }}
          </div>
          <!-- 删除按钮 -->
          <button
            @click.stop="handleDeleteConversation(conv.id)"
            class="absolute right-2 top-2 opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 text-sm p-1 transition-all"
            title="删除对话"
          >✕</button>
        </div>
      </div>

      <!-- 记忆面板 -->
      <MemoryPanel />

      <!-- 底部：用户信息 + 人格切换 -->
      <div class="p-4 border-t border-slate-700 space-y-3">
        <!-- 用户信息 -->
        <div class="flex items-center gap-2 text-sm">
          <span class="text-slate-400">{{ authStore.isAnonymous ? '👤 匿名用户' : '📧 ' + authStore.user?.email }}</span>
          <button
            @click="handleLogout"
            class="text-xs text-slate-500 hover:text-red-400 transition-colors ml-auto"
            title="退出登录"
          >退出</button>
        </div>

        <!-- 人格切换 -->
        <div 
          @click="showPersonaModal = true"
          class="flex items-center gap-2 cursor-pointer hover:bg-slate-700 p-2 rounded-lg transition-colors"
        >
          <span class="text-2xl">{{ currentPersonaEmoji }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-white truncate">{{ currentPersonaName }}</div>
            <div class="text-xs text-slate-400 truncate">{{ currentPersonaDesc }}</div>
          </div>
          <span class="text-slate-400 text-xs flex-shrink-0">切换 ▼</span>
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="flex-1 flex flex-col">
      <!-- 消息列表 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messageContainer">
        <div v-if="chatStore.messages.length === 0" class="text-center py-20">
          <div class="text-6xl mb-4">{{ currentPersonaEmoji }}</div>
          <h2 class="text-2xl font-bold text-white mb-2">你好，我是 {{ currentPersonaName }}</h2>
          <p class="text-slate-400">{{ currentPersonaDesc }}</p>
          <div class="mt-6 flex gap-2 justify-center">
            <button 
              v-for="prompt in quickPrompts" 
              :key="prompt"
              @click="sendQuickMessage(prompt)"
              class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-300 transition-colors"
            >
              {{ prompt }}
            </button>
          </div>
        </div>

        <div 
          v-for="msg in chatStore.messages" 
          :key="msg.id"
          :class="[
            'flex gap-3',
            msg.role === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <div 
            v-if="msg.role === 'assistant'"
            class="w-8 h-8 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center flex-shrink-0"
          >
            <span class="text-white text-sm">{{ currentPersonaEmoji }}</span>
          </div>

          <!-- 用户消息（可编辑） -->
          <div
            v-if="msg.role === 'user'"
            :class="[
              'max-w-[70%] rounded-2xl px-4 py-3 group relative',
              'bg-stardust-600 text-white rounded-br-md'
            ]"
          >
            <!-- 编辑模式 -->
            <div v-if="editingMessageId === msg.id" class="space-y-2">
              <textarea v-model="editContent" rows="3" class="w-full bg-stardust-700 border border-stardust-400 rounded-lg px-3 py-2 text-white text-sm resize-none focus:outline-none"></textarea>
              <div class="flex gap-2 justify-end">
                <button @click="cancelEdit" class="text-xs px-2 py-1 text-stardust-200 hover:text-white">取消</button>
                <button @click="saveEdit(msg.id)" :disabled="!editContent.trim()" class="text-xs px-3 py-1 bg-white text-stardust-600 rounded-lg hover:bg-stardust-100 disabled:opacity-50">保存并重新发送</button>
              </div>
            </div>
            <!-- 正常显示 -->
            <div v-else>
              <div class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</div>
              <!-- 操作按钮 -->
              <div class="flex gap-1 mt-2 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click="startEdit(msg)" class="text-xs text-stardust-200 hover:text-white p-1" title="编辑">✎</button>
                <button @click="copyMessage(msg.content)" class="text-xs text-stardust-200 hover:text-white p-1" :title="copiedId === msg.id ? '已复制' : '复制'">{{ copiedId === msg.id ? '✓' : '📋' }}</button>
              </div>
            </div>
          </div>

          <!-- AI 消息 -->
          <div
            v-else
            :class="[
              'max-w-[70%] rounded-2xl px-4 py-3 group relative',
              'bg-slate-700 text-slate-100 rounded-bl-md'
            ]"
          >
            <div class="markdown-body" v-html="renderMd(msg.content)"></div>
            <!-- 操作按钮 -->
            <div class="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button @click="copyMessage(msg.content)" class="text-xs text-slate-400 hover:text-white p-1" :title="copiedId === msg.id ? '已复制' : '复制'">{{ copiedId === msg.id ? '✓' : '📋' }}</button>
              <button v-if="isLastAiMsg(msg.id)" @click="handleRegenerate" class="text-xs text-slate-400 hover:text-white p-1" title="重新生成">🔄</button>
            </div>
          </div>

          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0"
          >
            <span class="text-white text-sm">我</span>
          </div>
        </div>

        <div v-if="chatStore.isLoading" class="flex gap-3 justify-start">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center flex-shrink-0">
            <span class="text-white text-sm">{{ currentPersonaEmoji }}</span>
          </div>
          <div class="bg-slate-700 rounded-2xl rounded-bl-md px-4 py-3">
            <div class="flex gap-1">
              <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
              <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="p-4 border-t border-slate-700 bg-slate-800/50">
        <div class="max-w-4xl mx-auto flex gap-2">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="sendMessage"
            placeholder="输入消息，按 Enter 发送..."
            rows="1"
            class="flex-1 bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 resize-none focus:outline-none focus:border-stardust-500 transition-colors"
            :disabled="chatStore.isLoading"
          ></textarea>
          <button
            v-if="chatStore.isLoading"
            @click="chatStore.abortGeneration()"
            class="px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl transition-colors text-sm font-medium"
          >
            ⏹ 停止
          </button>
          <button
            v-else
            @click="sendMessage"
            :disabled="!inputMessage.trim()"
            class="px-6 py-3 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
          >
            发送
          </button>
        </div>
      </div>
    </main>

    <!-- 人格切换弹窗 -->
    <PersonaSwitchModal
      :show="showPersonaModal"
      :current-id="chatStore.currentPersona?.id || 1"
      @close="showPersonaModal = false"
      @switch="handlePersonaSwitch"
      @create="showCreatePersonaModal = true"
    />

    <!-- 创建人格弹窗 -->
    <CreatePersonaModal
      :show="showCreatePersonaModal"
      @close="showCreatePersonaModal = false"
      @created="onPersonaCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { usePersonaStore } from '@/stores/persona'
import { useAuthStore } from '@/stores/auth'
import PersonaSwitchModal from '@/components/PersonaSwitchModal.vue'
import CreatePersonaModal from '@/components/CreatePersonaModal.vue'
import MemoryPanel from '@/components/MemoryPanel.vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch { /* fall through */ }
    }
    return '' // use external default escaping
  }
})

const router = useRouter()
const chatStore = useChatStore()
const personaStore = usePersonaStore()
const authStore = useAuthStore()
const inputMessage = ref('')
const messageContainer = ref<HTMLElement>()
const showPersonaModal = ref(false)
const showCreatePersonaModal = ref(false)
const editingMessageId = ref<number | null>(null)
const editContent = ref('')
const searchQuery = ref('')
const copiedId = ref<number | null>(null)

const filteredConversations = computed(() => {
  if (!searchQuery.value) return chatStore.conversations
  const q = searchQuery.value.toLowerCase()
  return chatStore.conversations.filter(c =>
    (c.title || '新对话').toLowerCase().includes(q)
  )
})

function renderMd(content: string): string {
  return md.render(content)
}

function isLastAiMsg(msgId: number): boolean {
  const msgs = chatStore.messages
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === 'assistant') return msgs[i].id === msgId
  }
  return false
}

async function copyMessage(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    // 找到这条消息的 id 标记已复制
    const lastAi = chatStore.messages.filter(m => m.role === 'assistant').pop()
    if (lastAi && lastAi.content === text) copiedId.value = lastAi.id
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch { /* ignore */ }
}

async function handleRegenerate() {
  if (chatStore.currentConversationId) {
    // 移除最后一条 AI 消息
    const msgs = chatStore.messages
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'assistant') {
        msgs.splice(i, 1)
        break
      }
    }
    await chatStore.regenerate(chatStore.currentConversationId)
  }
}

const quickPrompts = [
  '今天过得怎么样？',
  '我想聊聊心事',
  '给我讲个故事吧',
  '帮我记录一下...'
]

// 从 personaStore 获取当前人格信息（确保切换后同步）
const currentPersonaName = computed(() => {
  return personaStore.currentPersona?.name || chatStore.currentPersona?.name || '星尘'
})

const currentPersonaDesc = computed(() => {
  return personaStore.currentPersona?.description || chatStore.currentPersona?.description || '温柔陪伴'
})

const currentPersonaEmoji = computed(() => {
  const name = currentPersonaName.value
  const map: Record<string, string> = {
    '星尘': '✨',
    '北辰': '🌟',
    '阿星': '⭐'
  }
  return map[name] || '✨'
})

onMounted(async () => {
  // 检查认证状态
  if (authStore.token) {
    const valid = await authStore.checkAuth()
    if (!valid) {
      router.push('/auth')
      return
    }
  } else if (!authStore.isAuthenticated) {
    // 既没有 JWT，也不是匿名登录 → 去登录页
    router.push('/auth')
    return
  }

  // 初始化会话（同步匿名用户的 sessionId）
  if (authStore.isAnonymous && authStore.user?.session_id) {
    chatStore.sessionId = authStore.user.session_id
  }
  await chatStore.initSession()
  await chatStore.fetchConversations()
  await personaStore.fetchPersonas()
  // 同步人格信息
  await personaStore.fetchCurrentPersona(chatStore.sessionId)
})

async function handleLogout() {
  await authStore.logout()
  chatStore.createNewConversation()
  router.push('/auth')
}

watch(() => chatStore.messages.length, async () => {
  await nextTick()
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
})

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || chatStore.isLoading) return
  
  inputMessage.value = ''
  await chatStore.sendMessage(content)
}

const sendQuickMessage = async (prompt: string) => {
  await chatStore.sendMessage(prompt)
}

const loadConversation = async (id: number) => {
  await chatStore.fetchMessages(id)
}

const createNewChat = () => {
  chatStore.createNewConversation()
}

const handleDeleteConversation = async (id: number) => {
  if (!confirm('确定删除这条对话吗？')) return
  await chatStore.deleteConversation(id)
}

// 编辑消息
function startEdit(msg: { id: number; content: string }) {
  editingMessageId.value = msg.id
  editContent.value = msg.content
}

function cancelEdit() {
  editingMessageId.value = null
  editContent.value = ''
}

async function saveEdit(messageId: number) {
  if (!editContent.value.trim()) return

  const success = await chatStore.editMessage(messageId, editContent.value.trim())
  if (success) {
    chatStore.trimMessagesAfter(messageId)
    const msg = chatStore.messages.find(m => m.id === messageId)
    if (msg) msg.content = editContent.value.trim()
    cancelEdit()
    // 自动重新生成 AI 回复
    if (chatStore.currentConversationId) {
      await chatStore.regenerate(chatStore.currentConversationId)
    }
  }
}

const handlePersonaSwitch = async (personaId: number) => {
  await personaStore.switchPersona(personaId, chatStore.sessionId)
  await chatStore.fetchCurrentPersona()
  await personaStore.fetchCurrentPersona(chatStore.sessionId)
  showPersonaModal.value = false
}

const onPersonaCreated = async () => {
  await personaStore.fetchPersonas()
  showCreatePersonaModal.value = false
}

const formatDate = (dateStr: string) => {
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