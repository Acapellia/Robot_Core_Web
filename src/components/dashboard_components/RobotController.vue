<template>
  <div class="card">
    <div class="controller-body">Controller panel — buttons and controls.</div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.card { 
  height: 100%;   
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
}

.controller-body {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 1.4rem;
  font-weight: 600;
  text-align: center;
  padding: 12px;
  box-sizing: border-box;
}
</style>
