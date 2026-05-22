<template>
  <aside class="sidebar-area">
    <nav class="sidebar-menu">
      <ul>
        <li 
          :class="{ active: currentPath === '/robots' }" 
          @click="go('/robots')"
          title="Robot Control"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2" /><circle cx="12" cy="5" r="2" /><path d="M12 7v4" /><path d="M9 16h.01" /><path d="M15 16h.01" /></svg>
          <span class="menu-text">Robots</span>
        </li>

        <li 
          :class="{ active: currentPath === '/statistics' }" 
          @click="go('/statistics')"
          title="Statistics"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
          <span class="menu-text">Stats</span>
        </li>

        <li 
          :class="{ active: currentPath === '/settings' }" 
          @click="go('/settings')"
          title="Settings"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          <span class="menu-text">Settings</span>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const currentPath = computed(() => route.path)

const go = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.sidebar-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 72px;
  height: 100%;
  background-color: #f4f7fe;
  border-right: 1px solid #e9ecef;
  /* 상단 탑바 높이와 균형을 맞추기 위해 상단 패딩을 조정 */
  padding: 24px 0; 
  box-sizing: border-box;
}

.sidebar-menu {
  width: 100%;
}

.sidebar-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.sidebar-menu li {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  color: #8a92a6;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}

/* Hover 및 Active 스타일 유지 */
.sidebar-menu li:hover {
  color: #5c67f2;
  background-color: #f0f3ff;
}

.sidebar-menu li.active {
  color: #4338ca;
  background-color: #eef2ff;
  font-weight: 600;
}

/* Active 상태일 때 좌측 인디케이터 바 */
.sidebar-menu li.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 16px;
  bottom: 16px;
  width: 4px;
  background-color: #4338ca;
  border-radius: 0 4px 4px 0;
}

.menu-text {
  font-size: 10px;
  margin-top: 4px;
  font-weight: 500;
}
</style>