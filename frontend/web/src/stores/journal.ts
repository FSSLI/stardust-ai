import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api/v1'

export interface JournalEntry {
  id: number
  content: string
  entry_type: 'note' | 'todo' | 'mood' | 'memory'
  tags: string | null
  mood_score: number | null
  created_at: string
}

export interface JournalStats {
  total_entries: number
  by_type: Record<string, number>
  mood_trend: Array<{ date: string; avg_mood: number }>
}

export interface JournalFilters {
  entry_type: string
  date_from: string
  date_to: string
  tag: string
  page: number
  page_size: number
}

export const useJournalStore = defineStore('journal', () => {
  const entries = ref<JournalEntry[]>([])
  const stats = ref<JournalStats | null>(null)
  const isLoading = ref(false)
  const total = ref(0)

  const filters = reactive<JournalFilters>({
    entry_type: '',
    date_from: '',
    date_to: '',
    tag: '',
    page: 1,
    page_size: 20
  })

  function getAuthHeaders(): Record<string, string> {
    const authStore = useAuthStore()
    const headers: Record<string, string> = {}
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    // 兼容匿名用户
    const sessionId = localStorage.getItem('stardust_session_id')
    if (sessionId) {
      headers['X-Session-Id'] = sessionId
    }
    return headers
  }

  async function fetchEntries() {
    isLoading.value = true
    try {
      const params: Record<string, any> = {
        page: filters.page,
        page_size: filters.page_size
      }
      if (filters.entry_type) params.entry_type = filters.entry_type
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to
      if (filters.tag) params.tag = filters.tag

      const res = await axios.get(`${API_BASE}/journal`, {
        headers: getAuthHeaders(),
        params
      })
      entries.value = res.data.data.items || []
      total.value = res.data.data.total || 0
    } catch (e) {
      console.error('获取手帐列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStats() {
    try {
      const res = await axios.get(`${API_BASE}/journal/stats/summary`, {
        headers: getAuthHeaders()
      })
      stats.value = res.data.data
    } catch (e) {
      console.error('获取手帐统计失败:', e)
    }
  }

  async function createEntry(data: {
    content: string
    entry_type: string
    tags: string[]
    mood_score: number | null
  }): Promise<boolean> {
    isLoading.value = true
    try {
      await axios.post(`${API_BASE}/journal`, data, {
        headers: getAuthHeaders()
      })
      return true
    } catch (e) {
      console.error('创建手帐失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function updateEntry(
    entryId: number,
    data: {
      content?: string
      tags?: string[]
      mood_score?: number | null
    }
  ): Promise<boolean> {
    isLoading.value = true
    try {
      await axios.put(`${API_BASE}/journal/${entryId}`, data, {
        headers: getAuthHeaders()
      })
      return true
    } catch (e) {
      console.error('更新手帐失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteEntry(entryId: number): Promise<boolean> {
    try {
      await axios.delete(`${API_BASE}/journal/${entryId}`, {
        headers: getAuthHeaders()
      })
      return true
    } catch (e) {
      console.error('删除手帐失败:', e)
      return false
    }
  }

  function resetFilters() {
    filters.entry_type = ''
    filters.date_from = ''
    filters.date_to = ''
    filters.tag = ''
    filters.page = 1
  }

  return {
    entries,
    stats,
    isLoading,
    total,
    filters,
    fetchEntries,
    fetchStats,
    createEntry,
    updateEntry,
    deleteEntry,
    resetFilters
  }
})
