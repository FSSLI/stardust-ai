import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = '/api/v1'

export interface UserInfo {
  id: number
  email: string | null
  session_id: string | null
  current_persona_id: number
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string>(localStorage.getItem('stardust_token') || '')
  const isLoading = ref(false)
  const isAuthenticated = computed(() => !!user.value)
  const isAnonymous = computed(() => !!user.value && !user.value.email)

  function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {}
    if (token.value) {
      headers['Authorization'] = `Bearer ${token.value}`
    }
    return headers
  }

  /** 检查本地 token 是否有效 */
  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    try {
      const res = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      user.value = res.data.data
      return true
    } catch {
      // token 过期或无效
      logout()
      return false
    }
  }

  /** 邮箱注册 */
  async function register(email: string, password: string, code: string): Promise<string | null> {
    isLoading.value = true
    try {
      const res = await axios.post(`${API_BASE}/auth/register`, { email, password, code })
      const data = res.data.data
      setToken(data.access_token)
      user.value = data.user
      return null // 成功，无错误
    } catch (e: any) {
      const detail = e.response?.data?.detail || '注册失败'
      return detail
    } finally {
      isLoading.value = false
    }
  }

  /** 邮箱登录 */
  async function login(email: string, password: string): Promise<string | null> {
    isLoading.value = true
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { email, password })
      const data = res.data.data
      setToken(data.access_token)
      user.value = data.user
      return null
    } catch (e: any) {
      const detail = e.response?.data?.detail || '登录失败'
      return detail
    } finally {
      isLoading.value = false
    }
  }

  /** 匿名登录 */
  async function loginAnonymous(): Promise<boolean> {
    isLoading.value = true
    try {
      const res = await axios.post(`${API_BASE}/auth/anonymous`)
      const sessionId = res.data.data.session_id
      localStorage.setItem('stardust_session_id', sessionId)
      user.value = {
        id: res.data.data.user_id,
        email: null,
        session_id: sessionId,
        current_persona_id: 1,
        created_at: res.data.data.created_at
      }
      return true
    } catch (e) {
      console.error('匿名登录失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /** 登出 */
  async function logout() {
    // 通知后端清理（匿名用户会级联删除数据）
    try {
      await axios.post(`${API_BASE}/auth/logout`, {}, { headers: getAuthHeaders() })
    } catch {
      // 忽略网络错误
    }
    token.value = ''
    user.value = null
    localStorage.removeItem('stardust_token')
    localStorage.removeItem('stardust_session_id')
  }

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('stardust_token', t)
  }

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    isAnonymous,
    getAuthHeaders,
    checkAuth,
    register,
    login,
    loginAnonymous,
    logout
  }
})
