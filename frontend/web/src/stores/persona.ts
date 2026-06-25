import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = '/api/v1'

export interface Persona {
  id: number
  name: string
  avatar: string
  description: string
  is_default: boolean
  traits?: any
}

export const usePersonaStore = defineStore('persona', () => {
  const personas = ref<Persona[]>([])
  const currentPersona = ref<Persona | null>(null)
  const isLoading = ref(false)

  async function fetchPersonas() {
    isLoading.value = true
    try {
      const res = await axios.get(`${API_BASE}/personas`)
      console.log('获取人格数据:', res.data)
      // 后端返回 { data: { items: [...] } }
      personas.value = res.data.data.items || []
    } catch (e) {
      console.error('获取人格列表失败:', e)
      personas.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCurrentPersona(sessionId: string) {
    try {
      const res = await axios.get(`${API_BASE}/personas/current`, {
        headers: { 'X-Session-Id': sessionId }
      })
      currentPersona.value = res.data.data
    } catch (e) {
      console.error('获取当前人格失败:', e)
    }
  }

  async function switchPersona(personaId: number, sessionId: string) {
    isLoading.value = true
    try {
      const res = await axios.post(`${API_BASE}/personas/switch`, {
        persona_id: personaId
      }, {
        headers: { 'X-Session-Id': sessionId }
      })
      await fetchCurrentPersona(sessionId)
      return res.data
    } catch (e) {
      console.error('切换人格失败:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    personas,
    currentPersona,
    isLoading,
    fetchPersonas,
    fetchCurrentPersona,
    switchPersona
  }
})