<template>
  <div class="not-found av-page">
    <div class="not-found__inner av-scale-in">
      <div class="not-found__code av-gradient-text">404</div>
      <h1 class="not-found__title">{ $t('v.NotFound.2') }</h1>
      <p class="not-found__desc">{ $t('v.NotFound.0') }</p>
      <div class="not-found__actions">
        <el-button type="primary" size="large" round @click="$router.push('/boss')">
          <el-icon><HomeFilled /></el-icon>&nbsp;返回看板
        </el-button>
        <el-button size="large" round @click="$router.back()">{ $t('v.NotFound.3') }</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { HomeFilled } from '@element-plus/icons-vue'
</script>

<style scoped>
.not-found {
  height: 100%;
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.not-found__inner {
  text-align: center;
}
.not-found__code {
  font-size: 120px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  opacity: 0.9;
}
.not-found__title {
  font-size: 24px;
  margin: 8px 0 8px;
  color: var(--el-text-color-primary);
}
.not-found__desc {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 24px;
}
.not-found__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
