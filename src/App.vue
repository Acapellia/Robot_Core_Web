<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
}
</style>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRobotStore } from './stores/robotStore';
import { useEventStore } from './stores/eventStore';

onMounted(() => {
  useRobotStore().startMonitoring();
  useEventStore().startMonitoring();
});
</script>