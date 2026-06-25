<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="close">
    <div class="bg-slate-800 rounded-2xl p-6 w-full max-w-md mx-4 border border-slate-600">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-white">切换人格</h2>
        <button @click="close" class="text-slate-400 hover:text-white text-2xl leading-none">&times;</button>
      </div>

      <!-- Tab -->
      <div class="flex mb-4 bg-slate-700 rounded-lg p-1">
        <button @click="tab = 'system'"
          :class="['flex-1 py-1.5 rounded-md text-sm transition-colors', tab === 'system' ? 'bg-stardust-600 text-white' : 'text-slate-400']"
        >系统人格</button>
        <button @click="tab = 'custom'"
          :class="['flex-1 py-1.5 rounded-md text-sm transition-colors', tab === 'custom' ? 'bg-stardust-600 text-white' : 'text-slate-400']"
        >我的定制</button>
      </div>

      <!-- 加载中 -->
      <div v-if="personaStore.isLoading" class="text-center py-8 text-slate-400">加载中...</div>

      <!-- 系统人格列表 -->
      <div v-else-if="tab === 'system'" class="space-y-3">
        <div v-for="persona in systemPersonas" :key="persona.id"
          @click="selectPersona(persona.id)"
          :class="['p-4 rounded-xl border-2 cursor-pointer transition-all',
            selectedId === persona.id ? 'border-stardust-500 bg-stardust-900/30' : 'border-slate-600 hover:border-slate-500 bg-slate-700/50']">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-stardust-400 to-stardust-600 flex items-center justify-center text-xl">{{ getPersonaEmoji(persona.name) }}</div>
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

      <!-- 定制人格列表 -->
      <div v-else class="space-y-3">
        <div v-if="customPersonas.length === 0" class="text-center py-8 text-slate-500">
          <p class="mb-3">还没有定制人格</p>
        </div>
        <div v-for="persona in customPersonas" :key="persona.id"
          @click="selectPersona(persona.id)"
          :class="['p-4 rounded-xl border-2 cursor-pointer transition-all group',
            selectedId === persona.id ? 'border-stardust-500 bg-stardust-900/30' : 'border-slate-600 hover:border-slate-500 bg-slate-700/50']">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-600 flex items-center justify-center text-xl">🎨</div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-bold text-white truncate">{{ persona.name }}</h3>
                <span v-if="currentId === persona.id" class="text-xs bg-green-600 text-white px-2 py-0.5 rounded-full flex-shrink-0">当前</span>
              </div>
              <p class="text-sm text-slate-400 mt-1 truncate">{{ persona.description }}</p>
            </div>
            <button @click.stop="handleDelete(persona.id)"
              class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 text-sm p-1 transition-all flex-shrink-0" title="删除">🗑️</button>
          </div>
        </div>
        <!-- 创建按钮 -->
        <button @click="$emit('create')"
          class="w-full py-3 border-2 border-dashed border-slate-600 rounded-xl text-slate-400 hover:border-stardust-500 hover:text-stardust-400 transition-colors text-sm">
          + 创建定制人格
        </button>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <button @click="close" class="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm">取消</button>
        <button @click="confirmSwitch" :disabled="!selectedId || selectedId === currentId"
          class="px-5 py-2 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg text-sm">
          确认切换
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePersonaStore } from '@/stores/persona'

const props = defineProps<{ show: boolean; currentId: number }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'switch', personaId: number): void; (e: 'create'): void }>()

const personaStore = usePersonaStore()
const selectedId = ref<number | null>(null)
const tab = ref<'system' | 'custom'>('system')

const systemPersonas = computed(() => personaStore.personas.filter(p => p.is_system !== false))
const customPersonas = computed(() => personaStore.personas.filter(p => p.is_system === false))

watch(() => props.show, async (newVal) => {
  if (newVal) {
    selectedId.value = props.currentId
    tab.value = 'system'
    await personaStore.fetchPersonas()
  }
}, { immediate: true })

const selectPersona = (id: number) => { selectedId.value = id }

const confirmSwitch = () => {
  if (selectedId.value && selectedId.value !== props.currentId) {
    emit('switch', selectedId.value)
  }
}

const close = () => { selectedId.value = null; emit('close') }

const handleDelete = async (id: number) => {
  if (!confirm('确定删除这个定制人格吗？')) return
  await personaStore.deleteCustomPersona(id)
  await personaStore.fetchPersonas()
}

const getPersonaEmoji = (name: string) => {
  const map: Record<string, string> = { '星尘': '✨', '北辰': '🌟', '阿星': '⭐' }
  return map[name] || '✨'
}
</script>
