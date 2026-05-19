<template>
  <aside class="sidebar-area">
    <nav class="sidebar-menu">
      <ul>
        <li @click="go('/')">Dashboard</li>
        <li @click="go('/other')">Other Page</li>
      </ul>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
const go = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
/* local tweaks; main spacing in layout.css */
.sidebar-area {
  height: 100%;
}
</style>
