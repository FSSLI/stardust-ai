import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

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

  // Getters
  const currentMessages = computed(() => messages.value)

  // Actions
  async function initSession() {
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
        headers: { 'X-Session-Id': sessionId.value }
      })
      currentPersona.value = res.data.data
    } catch (e) {
      console.error('获取当前人格失败:', e)
    }
  }

  async function fetchConversations() {
    try {
      const res = await axios.get(`${API_BASE}/chat/conversations`, {
        headers: { 'X-Session-Id': sessionId.value }
      })
      conversations.value = res.data.data.items
    } catch (e) {
      console.error('获取对话列表失败:', e)
    }
  }

  async function fetchMessages(conversationId: number) {
    try {
      const res = await axios.get(`${API_BASE}/chat/conversations/${conversationId}`, {
        headers: { 'X-Session-Id': sessionId.value }
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

    // SSE 流式请求
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Id': sessionId.value
      },
      body: JSON.stringify(payload)
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let aiContent = ''

    // 添加 AI 消息占位
    const aiMsg: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    messages.value.push(aiMsg)

    while (reader) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const event = JSON.parse(data)
            
            if (event.type === 'content' && event.content) {
              aiContent += event.content
              aiMsg.content = aiContent
            } else if (event.type === 'done') {
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

    isLoading.value = false
    await fetchConversations()
  }

  async function createNewConversation() {
    currentConversationId.value = null
    messages.value = []
  }

  async function deleteConversation(id: number) {
    try {
      await axios.delete(`${API_BASE}/chat/conversations/${id}`, {
        headers: { 'X-Session-Id': sessionId.value }
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
    createNewConversation,
    deleteConversation
  }
})