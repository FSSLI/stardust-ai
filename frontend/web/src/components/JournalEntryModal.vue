<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="close">
    <div class="bg-slate-800 rounded-2xl p-6 w-full max-w-lg mx-4 border border-slate-600 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white">{{ isEdit ? '编辑记录' : '新建记录' }}</h2>
        <button @click="close" class="text-slate-400 hover:text-white text-2xl leading-none">&times;</button>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- 类型选择 -->
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">类型</label>
          <div class="grid grid-cols-4 gap-2">
            <button
              v-for="t in entryTypes"
              :key="t.value"
              type="button"
              @click="form.entry_type = t.value"
              :class="[
                'py-2 px-3 rounded-lg text-sm font-medium transition-colors border-2',
                form.entry_type === t.value
                  ? 'border-stardust-500 bg-stardust-900/30 text-white'
                  : 'border-slate-600 text-slate-400 hover:border-slate-500'
              ]"
            >
              <span class="mr-1">{{ t.emoji }}</span>
              {{ t.label }}
            </button>
          </div>
        </div>

        <!-- 内容 -->
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">内容</label>
          <textarea
            v-model="form.content"
            rows="4"
            placeholder="写点什么..."
            class="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 resize-none focus:outline-none focus:border-stardust-500 transition-colors"
            required
          ></textarea>
        </div>

        <!-- 心情评分 -->
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">
            心情评分
            <span class="text-slate-500 font-normal ml-1">{{ form.mood_score ? form.mood_score + '分' : '未设置' }}</span>
          </label>
          <div class="flex items-center gap-1">
            <button
              v-for="score in 10"
              :key="score"
              type="button"
              @click="form.mood_score = form.mood_score === score ? null : score"
              :class="[
                'w-9 h-9 rounded-lg text-lg transition-all',
                form.mood_score && form.mood_score >= score
                  ? 'bg-stardust-600 scale-110'
                  : 'bg-slate-700 opacity-50 hover:opacity-80'
              ]"
              :title="score + '分'"
            >
              {{ moodEmoji(score) }}
            </button>
          </div>
        </div>

        <!-- 标签 -->
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">
            标签
            <span class="text-slate-500 font-normal">（逗号分隔）</span>
          </label>
          <input
            v-model="tagsInput"
            type="text"
            placeholder="例如：工作, 学习, 生活"
            class="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-stardust-500 transition-colors"
          />
        </div>

        <!-- 按钮 -->
        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            @click="close"
            class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            type="submit"
            :disabled="!form.content.trim() || isLoading"
            class="px-5 py-2.5 bg-stardust-600 hover:bg-stardust-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            {{ isLoading ? '保存中...' : isEdit ? '更新' : '创建' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useJournalStore } from '@/stores/journal'

const props = defineProps<{
  show: boolean
  editEntry?: {
    id: number
    content: string
    entry_type: string
    tags: string | null
    mood_score: number | null
  } | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const journalStore = useJournalStore()
const isLoading = ref(false)

const isEdit = computed(() => !!props.editEntry)

const entryTypes = [
  { value: 'note', label: '笔记', emoji: '📝' },
  { value: 'todo', label: '待办', emoji: '✅' },
  { value: 'mood', label: '心情', emoji: '💭' },
  { value: 'memory', label: '回忆', emoji: '💾' }
]

const form = reactive({
  content: '',
  entry_type: 'note',
  mood_score: null as number | null,
})

const tagsInput = ref('')

// 监听弹窗打开，初始化表单
watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.editEntry) {
      form.content = props.editEntry.content
      form.entry_type = props.editEntry.entry_type
      form.mood_score = props.editEntry.mood_score
      tagsInput.value = props.editEntry.tags || ''
    } else {
      form.content = ''
      form.entry_type = 'note'
      form.mood_score = null
      tagsInput.value = ''
    }
  }
})

function moodEmoji(score: number): string {
  if (score <= 2) return '😞'
  if (score <= 4) return '😕'
  if (score <= 6) return '😐'
  if (score <= 8) return '🙂'
  return '😊'
}

function parseTags(): string[] {
  return tagsInput.value
    .split(/[,，]/)
    .map(t => t.trim())
    .filter(t => t.length > 0)
}

async function handleSubmit() {
  if (!form.content.trim()) return

  isLoading.value = true
  let success = false

  const data = {
    content: form.content.trim(),
    entry_type: form.entry_type,
    tags: parseTags(),
    mood_score: form.mood_score
  }

  if (isEdit.value && props.editEntry) {
    success = await journalStore.updateEntry(props.editEntry.id, data)
  } else {
    success = await journalStore.createEntry(data)
  }

  isLoading.value = false

  if (success) {
    emit('saved')
    close()
  }
}

function close() {
  emit('close')
}
</script>
