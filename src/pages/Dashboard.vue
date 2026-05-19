<template>
  <div class="dashboard" style="height:100%; display:grid; grid-template-rows: 1fr 1fr; gap:12px;">
    <ContentTopGrid />
    <ContentBottom />
  </div>
</template>

<script setup lang="ts">
import ContentTopGrid from '../components/ContentTopGrid.vue'
import ContentBottom from '../components/ContentBottom.vue'
</script>

<style scoped></style>
