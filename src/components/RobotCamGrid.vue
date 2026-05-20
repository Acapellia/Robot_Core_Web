<template>
  <div class="top-grid">
    <div v-for="i in 6" :key="i" class="card">Camera {{ i }}</div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.top-grid { height: 100%; }
.card { 
  height: 100%; 
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
}
</style>
