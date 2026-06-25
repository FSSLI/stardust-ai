import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api/v1'

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  persona_id: number
  updated_at: string
}

export const useChatStore = defineStore('chat', () => {
  // State
  const sessionId = ref<string>(localStorage.getItem('stardust_session_id') || '')
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const currentPersona = ref<any>(null)
  let abortController: AbortController | null = null

  // Getters
  const currentMessages = computed(() => messages.value)

  function getAuthHeaders(): Record<string, string> {
    const authStore = useAuthStore()
    const headers: Record<string, string> = {}
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    if (sessionId.value) {
      headers['X-Session-Id'] = sessionId.value
    }
    return headers
  }

  // Actions
  async function initSession() {
    const authStore = useAuthStore()
    // 已注册用户跳过匿名 session 创建
    if (authStore.token) {
      await fetchCurrentPersona()
      return
    }
    // 匿名用户：优先从 localStorage 同步（可能由 authStore 在其他时机写入）
    if (!sessionId.value) {
      const stored = localStorage.getItem('stardust_session_id')
      if (stored) {
        sessionId.value = stored
      }
    }
    if (!sessionId.value) {
      const res = await axios.post(`${API_BASE}/auth/anonymous`)
      sessionId.value = res.data.data.session_id
      localStorage.setItem('stardust_session_id', sessionId.value)
    }
    // 获取当前人格
    await fetchCurrentPersona()
  }

  async function fetchCurrentPersona() {
    try {
      const res = await axios.get(`${API_BASE}/personas/current`, {
        headers: getAuthHeaders()
      })
      currentPersona.value = res.data.data
    } catch (e) {
      console.error('获取当前人格失败:', e)
    }
  }

  async function fetchConversations() {
    try {
      const res = await axios.get(`${API_BASE}/chat/conversations`, {
        headers: getAuthHeaders()
      })
      conversations.value = res.data.data.items
    } catch (e) {
      console.error('获取对话列表失败:', e)
    }
  }

  async function fetchMessages(conversationId: number) {
    try {
      const res = await axios.get(`${API_BASE}/chat/conversations/${conversationId}`, {
        headers: getAuthHeaders()
      })
      messages.value = res.data.data.messages
      currentConversationId.value = conversationId
    } catch (e) {
      console.error('获取消息失败:', e)
    }
  }

  async function sendMessage(content: string, personaId?: number) {
    isLoading.value = true
    
    // 先添加用户消息到本地
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    }
    messages.value.push(userMsg)

    // 创建新对话或继续现有对话
    const payload = {
      message: content,
      persona_id: personaId || currentPersona.value?.id,
      conversation_id: currentConversationId.value
    }

    // SSE 流式请求（支持中断）
    abortController = new AbortController()
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(payload),
      signal: abortController.signal
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let rawBuffer = ''       // SSE 快速收数据
    let streamDone = false

    // 添加 AI 消息占位
    const aiMsg: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    messages.value.push(aiMsg)

    // 打字机效果：逐字从缓冲区输出
    const typeSpeed = 30  // 毫秒/字
    let displayIndex = 0
    const typeInterval = setInterval(() => {
      if (displayIndex < rawBuffer.length) {
        displayIndex++
        aiMsg.content = rawBuffer.substring(0, displayIndex)
      }
      if (streamDone && displayIndex >= rawBuffer.length) {
        clearInterval(typeInterval)
        isLoading.value = false
        fetchConversations()
      }
    }, typeSpeed)

    // 读取 SSE 流
    try {
      while (reader) {
        const { done, value } = await reader.read()
        if (done) { streamDone = true; break }

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const event = JSON.parse(data)

              if (event.type === 'content' && event.content) {
                rawBuffer += event.content     // 追加到缓冲区
              } else if (event.type === 'done') {
                streamDone = true
                // 用服务端真实 ID 替换客户端临时 ID
                if (event.user_message_id) {
                  userMsg.id = event.user_message_id
                }
                if (event.conversation_id) {
                  currentConversationId.value = event.conversation_id
                }
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch {
      streamDone = true
    }

    // 确保流结束（兜底）
    if (!streamDone) {
      streamDone = true
    }
  }

  async function editMessage(messageId: number, newContent: string) {
    try {
      await axios.put(
        `${API_BASE}/chat/messages/${messageId}`,
        { content: newContent },
        { headers: getAuthHeaders() }
      )
      return true
    } catch (e) {
      console.error('编辑消息失败:', e)
      return false
    }
  }

  /** 从本地消息列表中移除某条消息及其之后的所有消息 */
  function trimMessagesAfter(messageId: number) {
    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx !== -1) {
      messages.value = messages.value.slice(0, idx + 1)
    }
  }

  /** 基于当前对话自动生成 AI 回复（不添加新用户消息） */
  async function regenerate(conversationId: number) {
    isLoading.value = true

    // 添加 AI 消息占位
    const aiMsg: Message = {
      id: Date.now(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    messages.value.push(aiMsg)

    let rawBuffer = ''
    let streamDone = false
    let displayIndex = 0

    const typeInterval = setInterval(() => {
      if (displayIndex < rawBuffer.length) {
        displayIndex++
        aiMsg.content = rawBuffer.substring(0, displayIndex)
      }
      if (streamDone && displayIndex >= rawBuffer.length) {
        clearInterval(typeInterval)
        isLoading.value = false
      }
    }, 30)

    abortController = new AbortController()
    try {
      const response = await fetch(`${API_BASE}/chat/regenerate/${conversationId}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        signal: abortController.signal
      })
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      while (reader) {
        const { done, value } = await reader.read()
        if (done) { streamDone = true; break }

        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'content' && event.content) {
                rawBuffer += event.content
              } else if (event.type === 'done') {
                streamDone = true
              }
            } catch {}
          }
        }
      }
    } catch {
      streamDone = true
    }
  }

  function abortGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isLoading.value = false
  }

  async function createNewConversation() {
    currentConversationId.value = null
    messages.value = []
  }

  async function deleteConversation(id: number) {
    try {
      await axios.delete(`${API_BASE}/chat/conversations/${id}`, {
        headers: getAuthHeaders()
      })
      if (currentConversationId.value === id) {
        createNewConversation()
      }
      await fetchConversations()
    } catch (e) {
      console.error('删除对话失败:', e)
    }
  }

  return {
    sessionId,
    conversations,
    currentConversationId,
    messages,
    isLoading,
    currentPersona,
    currentMessages,
    initSession,
    fetchCurrentPersona,
    fetchConversations,
    fetchMessages,
    sendMessage,
    abortGeneration,
    editMessage,
    trimMessagesAfter,
    regenerate,
    createNewConversation,
    deleteConversation
  }
})