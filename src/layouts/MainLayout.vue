<template>
  <div class="app-container">
    <Header />

    <div class="middle">
      <SidebarMenu />

      <main class="content-area">
        <router-view />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import Header from '../components/fixed_components/Header.vue'
import Footer from '../components/fixed_components/Footer.vue'
import SidebarMenu from '../components/fixed_components/SidebarMenu.vue'
</script>

<style scoped>
@import '../styles/layout.css';
</style>
