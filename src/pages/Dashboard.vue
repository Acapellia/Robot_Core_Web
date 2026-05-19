<template>
  <div class="dashboard">
    <ContentTopGrid class="content-top" />
    <ContentBottom class="content-bottom" />
  </div>
</template>

<script setup lang="ts">
import ContentTopGrid from '../components/ContentTopGrid.vue'
import ContentBottom from '../components/ContentBottom.vue'
</script>

<style scoped>
.dashboard {
  height: 100%;
  display: grid;

  /* ⭐ 수정: 잘못된 calc 방식을 지우고 변수를 직접 매핑 */
  grid-template-rows: var(--content-top-ratio) var(--content-bottom-ratio);

  gap: var(--content-top-bottom-gap);
}

.content-top,
.content-bottom {
  min-height: 0;
  overflow: hidden;
}
</style>