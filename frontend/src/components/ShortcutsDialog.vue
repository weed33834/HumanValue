<template>
  <el-dialog v-model="visible" :title="t('shortcut.title')" width="520px" append-to-body>
    <div class="shortcuts-list">
      <div v-for="(group, gi) in groups" :key="gi" class="shortcut-group">
        <div class="shortcut-group__title">{{ group.title }}</div>
        <div v-for="(item, i) in group.items" :key="i" class="shortcut-row">
          <span class="shortcut-desc">{{ item.desc }}</span>
          <span class="shortcut-keys">
            <kbd v-for="(k, ki) in item.keys" :key="ki" class="av-kbd">{{ k }}</kbd>
          </span>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const visible = ref(false)
const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
watch(
  () => props.modelValue,
  (v) => (visible.value = v),
)
watch(visible, (v) => emit('update:modelValue', v))

const emit = defineEmits(['update:modelValue'])

const groups = computed(() => [
  {
    title: t('shortcut.general'),
    items: [
      { desc: t('shortcut.openPalette'), keys: ['Ctrl', 'K'] },
      { desc: t('shortcut.openShortcuts'), keys: ['Ctrl', '/'] },
      { desc: t('shortcut.closeDialog'), keys: ['Esc'] },
      { desc: t('shortcut.toggleTheme'), keys: ['Ctrl', 'Shift', 'D'] },
    ],
  },
  {
    title: t('shortcut.chat'),
    items: [
      { desc: t('shortcut.sendMsg'), keys: ['Enter'] },
      { desc: t('shortcut.newline'), keys: ['Shift', 'Enter'] },
      { desc: t('shortcut.sendMsg'), keys: ['Ctrl', 'Enter'] },
      { desc: t('shortcut.stopGen'), keys: ['Esc'] },
    ],
  },
  {
    title: t('shortcut.nav'),
    items: [
      { desc: t('shortcut.backPage'), keys: ['Alt', '←'] },
      { desc: t('shortcut.forwardPage'), keys: ['Alt', '→'] },
    ],
  },
])
</script>

<style scoped>
.shortcuts-list {
  max-height: 60vh;
  overflow-y: auto;
}
.shortcut-group {
  margin-bottom: 18px;
}
.shortcut-group__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.04em;
}
.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 4px;
  border-radius: 6px;
  transition: background 0.15s;
}
.shortcut-row:hover {
  background: var(--el-fill-color-light);
}
.shortcut-desc {
  font-size: 13px;
  color: var(--el-text-color-primary);
}
.shortcut-keys {
  display: flex;
  gap: 4px;
}
</style>
