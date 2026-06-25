<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="close">
    <div class="bg-slate-800 rounded-2xl p-6 w-full max-w-md mx-4 border border-slate-600">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white">切换人格</h2>
        <button @click="close" class="text-slate-400 hover:text-white text-2xl">&times;</button>
      </div>

      <!-- 加载中 -->
      <div v-if="personaStore.isLoading" class="text-center py-8 text-slate-400">
        加载中...
      </div>

      <!-- 人格列表 -->
      <div v-else-if="personaStore.personas && personaStore.personas.length > 0" class="space-y-3">
        <div
          v-for="persona in personaStore.personas"
          :key="persona.id"
          @click="selectPersona(persona.id)"
          :class="[
            'p-4 rounded-xl border-2 cursor-pointer transition-all',
            selectedId === persona.id
              ? 'border-stardust-500 bg-stardust-900/30'
              : 'border-slate-600 hover:border-slate-500 bg-slate-700/50'
          ]"
        >
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center text-2xl">
              {{ getPersonaEmoji(persona.name) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <h3 class="font-bold text-white">{{ persona.name }}</h3>
                <span v-if="persona.is_default" class="text-xs bg-stardust-600 text-white px-2 py-0.5 rounded-full">默认</span>
                <span v-if="currentId === persona.id" class="text-xs bg-green-600 text-white px-2 py-0.5 rounded-full">当前</span>
              </div>
              <p class="text-sm text-slate-400 mt-1">{{ persona.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-8 text-slate-400">
        暂无人格数据
        <div class="text-xs mt-2 text-slate-500">debug: personas={{ personaStore.personas?.length || 0 }}</div>
      </div>

      <div class="mt-6 flex justify-end">
        <button
          @click="confirmSwitch"
          :disabled="!selectedId || selectedId === currentId || personaStore.isLoading"
          class="px-6 py-2 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          {{ personaStore.isLoading ? '切换中...' : '确认切换' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { usePersonaStore } from '@/stores/persona'

const props = defineProps<{
  show: boolean
  currentId: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'switch', personaId: number): void
}>()

const personaStore = usePersonaStore()
const selectedId = ref<number | null>(null)

// 监听 show 变化
watch(() => props.show, async (newVal) => {
  console.log('弹窗显示状态:', newVal)
  if (newVal) {
    selectedId.value = props.currentId
    console.log('开始获取人格数据...')
    await personaStore.fetchPersonas()
    console.log('人格数据获取完成:', personaStore.personas)
  }
}, { immediate: true })

const selectPersona = (id: number) => {
  selectedId.value = id
}

const confirmSwitch = () => {
  if (selectedId.value && selectedId.value !== props.currentId) {
    emit('switch', selectedId.value)
  }
}

const close = () => {
  selectedId.value = null
  emit('close')
}

const getPersonaEmoji = (name: string) => {
  const map: Record<string, string> = {
    '星尘': '✨',
    '北辰': '🌟',
    '阿星': '⭐'
  }
  return map[name] || '✨'
}
</script>