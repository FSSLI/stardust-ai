import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api/v1'

export interface Persona {
  id: number
  name: string
  avatar: string
  description: string
  is_default: boolean
  is_system?: boolean
  user_id?: number | null
  traits?: any
}

export const usePersonaStore = defineStore('persona', () => {
  const personas = ref<Persona[]>([])
  const currentPersona = ref<Persona | null>(null)
  const isLoading = ref(false)

  function getAuthHeaders(): Record<string, string> {
    const authStore = useAuthStore()
    const headers: Record<string, string> = {}
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    const sessionId = localStorage.getItem('stardust_session_id')
    if (sessionId) {
      headers['X-Session-Id'] = sessionId
    }
    return headers
  }

  async function fetchPersonas() {
    isLoading.value = true
    try {
      const res = await axios.get(`${API_BASE}/personas`, {
        headers: getAuthHeaders()
      })
      personas.value = res.data.data.items || []
    } catch (e) {
      console.error('获取人格列表失败:', e)
      personas.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCurrentPersona(_sessionId?: string) {
    try {
      const res = await axios.get(`${API_BASE}/personas/current`, {
        headers: getAuthHeaders()
      })
      currentPersona.value = res.data.data
    } catch (e) {
      console.error('获取当前人格失败:', e)
    }
  }

  async function switchPersona(personaId: number, _sessionId?: string) {
    isLoading.value = true
    try {
      const res = await axios.post(`${API_BASE}/personas/switch`, {
        persona_id: personaId
      }, {
        headers: getAuthHeaders()
      })
      await fetchCurrentPersona()
      return res.data
    } catch (e) {
      console.error('切换人格失败:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function createPersonaFromDescription(desc: string): Promise<boolean> {
    isLoading.value = true
    try {
      const formData = new FormData()
      formData.append('description', desc)
      await axios.post(`${API_BASE}/personas/custom`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
      })
      return true
    } catch (e) {
      console.error('创建人格失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function createPersonaFromFile(file: File, desc: string): Promise<boolean> {
    isLoading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (desc) formData.append('description', desc)
      await axios.post(`${API_BASE}/personas/custom/upload`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
      })
      return true
    } catch (e) {
      console.error('上传创建人格失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCustomPersona(personaId: number): Promise<boolean> {
    try {
      await axios.delete(`${API_BASE}/personas/custom/${personaId}`, {
        headers: getAuthHeaders()
      })
      return true
    } catch (e) {
      console.error('删除人格失败:', e)
      return false
    }
  }

  return {
    personas,
    currentPersona,
    isLoading,
    fetchPersonas,
    fetchCurrentPersona,
    switchPersona,
    createPersonaFromDescription,
    createPersonaFromFile,
    deleteCustomPersona
  }
})