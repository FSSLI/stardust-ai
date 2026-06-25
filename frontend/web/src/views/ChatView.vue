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

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto p-2">
        <div 
          v-for="conv in chatStore.conversations" 
          :key="conv.id"
          @click="loadConversation(conv.id)"
          :class="[
            'p-3 rounded-lg cursor-pointer mb-1 transition-colors',
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
        </div>
      </div>

      <!-- 底部：人格切换 -->
      <div class="p-4 border-t border-slate-700">
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

          <div 
            :class="[
              'max-w-[70%] rounded-2xl px-4 py-3',
              msg.role === 'user' 
                ? 'bg-stardust-600 text-white rounded-br-md' 
                : 'bg-slate-700 text-slate-100 rounded-bl-md'
            ]"
          >
            <div class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</div>
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
            @click="sendMessage"
            :disabled="!inputMessage.trim() || chatStore.isLoading"
            class="px-6 py-3 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
          >
            <span v-if="!chatStore.isLoading">发送</span>
            <span v-else>...</span>
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
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { usePersonaStore } from '@/stores/persona'
import PersonaSwitchModal from '@/components/PersonaSwitchModal.vue'

const chatStore = useChatStore()
const personaStore = usePersonaStore()
const inputMessage = ref('')
const messageContainer = ref<HTMLElement>()
const showPersonaModal = ref(false)

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
  await chatStore.initSession()
  await chatStore.fetchConversations()
  await personaStore.fetchPersonas()
  // 同步人格信息
  await personaStore.fetchCurrentPersona(chatStore.sessionId)
})

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

const handlePersonaSwitch = async (personaId: number) => {
  await personaStore.switchPersona(personaId, chatStore.sessionId)
  // 同步更新 chatStore 中的人格信息
  await chatStore.fetchCurrentPersona()
  // 同时更新 personaStore
  await personaStore.fetchCurrentPersona(chatStore.sessionId)
  showPersonaModal.value = false
  // 切换人格后创建新对话
  chatStore.createNewConversation()
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