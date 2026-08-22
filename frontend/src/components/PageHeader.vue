<template>
  <div class="av-page-header">
    <div class="av-page-header__left">
      <h1 class="av-page-header__title">
        <slot name="icon"></slot>
        <span>{{ title }}</span>
        <slot name="tag"></slot>
      </h1>
      <p v-if="subtitle" class="av-page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="av-page-header__actions">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
// 统一页面头部: 标题 + 副标题 + 右侧操作区。
// 用法: <PageHeader title="团队分析" subtitle="按部门聚合的风险与产出">
//         <el-button type="primary">导出</el-button>
//       </PageHeader>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
