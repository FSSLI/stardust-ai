import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import JournalView from '../views/JournalView.vue'
import AuthView from '../views/AuthView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true }
    },
    {
      path: '/journal',
      name: 'journal',
      component: JournalView,
      meta: { requiresAuth: true }
    },
    {
      path: '/auth',
      name: 'auth',
      component: AuthView
    }
  ]
})

export default router