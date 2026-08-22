<template>
  <div class="av-empty">
    <div class="av-empty__icon">
      <slot name="icon"
        ><el-icon><InfoFilled /></el-icon
      ></slot>
    </div>
    <div v-if="title" class="av-empty__title">{{ title }}</div>
    <p v-if="description" class="av-empty__desc">{{ description }}</p>
    <div v-if="$slots.action" class="av-empty__action"><slot name="action"></slot></div>
  </div>
</template>

<script setup>
import { InfoFilled } from '@element-plus/icons-vue'
// 统一空状态: 图标 + 标题 + 描述 + 引导动作。
// 用法: <EmptyState title="暂无数据" description="可以……" ><template #action><el-button>去创建</el-button></template></EmptyState>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>
