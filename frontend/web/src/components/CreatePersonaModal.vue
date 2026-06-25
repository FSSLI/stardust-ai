<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="close">
    <div class="bg-slate-800 rounded-2xl p-6 w-full max-w-lg mx-4 border border-slate-600 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white">创建定制人格</h2>
        <button @click="close" class="text-slate-400 hover:text-white text-2xl leading-none">&times;</button>
      </div>

      <!-- Tab 切换创建方式 -->
      <div class="flex mb-5 bg-slate-700 rounded-lg p-1">
        <button
          v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
          :class="['flex-1 py-2 rounded-md text-sm font-medium transition-colors', activeTab === tab.key ? 'bg-stardust-600 text-white' : 'text-slate-400 hover:text-white']"
        >{{ tab.label }}</button>
      </div>

      <!-- 方式一：文字描述 -->
      <div v-if="activeTab === 'describe'" class="space-y-4">
        <div>
          <label class="block text-sm text-slate-300 mb-2">描述你想要的角色</label>
          <textarea v-model="describeText" rows="4" placeholder="例如：一个像林黛玉一样多愁善感、心思细腻的角色，喜欢用诗词表达情感..."
            class="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:border-stardust-500"></textarea>
        </div>
        <button @click="submitDescribe" :disabled="!describeText.trim() || loading"
          class="w-full py-3 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-xl font-medium">
          {{ loading ? 'AI 生成中...' : '✨ AI 生成人格' }}
        </button>
      </div>

      <!-- 方式二：文件上传 -->
      <div v-if="activeTab === 'file'" class="space-y-4">
        <label
          class="block border-2 border-dashed border-slate-600 rounded-xl p-8 text-center cursor-pointer hover:border-stardust-500 transition-colors"
          @dragover.prevent @drop.prevent="onDrop">
          <input type="file" accept=".txt,.docx,.pdf" class="hidden" ref="fileInput" @change="onFileChange" />
          <div v-if="!selectedFile" class="text-slate-400">
            <div class="text-4xl mb-2">📁</div>
            <p>点击或拖拽上传文件</p>
            <p class="text-xs mt-1">支持 txt / docx / pdf</p>
          </div>
          <div v-else class="text-white">
            <div class="text-2xl mb-1">📄</div>
            <p>{{ selectedFile.name }}</p>
            <p class="text-xs text-slate-400 mt-1">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
          </div>
        </label>
        <input v-model="fileDesc" placeholder="额外要求（可选）：希望角色更温柔一些..."
          class="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-stardust-500 text-sm" />
        <button @click="submitFile" :disabled="!selectedFile || loading"
          class="w-full py-3 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-xl font-medium">
          {{ loading ? '分析中...' : '📖 分析文件创建人格' }}
        </button>
      </div>

      <!-- 结果 -->
      <div v-if="errorMsg" class="mt-4 bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">{{ errorMsg }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePersonaStore } from '@/stores/persona'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'created'): void }>()

const personaStore = usePersonaStore()
const activeTab = ref<'describe' | 'file'>('describe')
const loading = ref(false)
const errorMsg = ref('')

const describeText = ref('')
const selectedFile = ref<File | null>(null)
const fileDesc = ref('')
const fileInput = ref<HTMLInputElement>()

const tabs = [
  { key: 'describe' as const, label: '📝 文字描述' },
  { key: 'file' as const, label: '📁 文件上传' }
]

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) selectedFile.value = input.files[0]
}

function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file) selectedFile.value = file
}

async function submitDescribe() {
  if (!describeText.value.trim()) return
  loading.value = true; errorMsg.value = ''
  const ok = await personaStore.createPersonaFromDescription(describeText.value.trim())
  loading.value = false
  if (ok) { emit('created'); close() }
  else errorMsg.value = '创建失败，请重试'
}

async function submitFile() {
  if (!selectedFile.value) return
  loading.value = true; errorMsg.value = ''
  const ok = await personaStore.createPersonaFromFile(selectedFile.value, fileDesc.value)
  loading.value = false
  if (ok) { emit('created'); close() }
  else errorMsg.value = '分析失败，请检查文件格式'
}

function close() {
  describeText.value = ''
  selectedFile.value = null
  fileDesc.value = ''
  errorMsg.value = ''
  emit('close')
}
</script>
