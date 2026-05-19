<template>
  <div class="dashboard" style="height:100%; display:grid; grid-template-rows: calc(var(--content-top-ratio) * 1fr) calc(var(--content-bottom-ratio) * 1fr); row-gap: var(--content-top-bottom-gap);">
    <ContentTopGrid />
    <ContentBottom />
  </div>
</template>

<script setup lang="ts">
import ContentTopGrid from '../components/ContentTopGrid.vue'
import ContentBottom from '../components/ContentBottom.vue'
</script>

<style scoped></style>
