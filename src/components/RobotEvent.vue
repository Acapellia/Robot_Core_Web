<template>
  <div class="card event-stream-container">
    <div class="header">
      <h3 class="title">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12h3l3-9 4 18 3-13 1 4h4" />
        </svg>
        EVENT STREAM
      </h3>
    </div>

    <div class="main-content">
      <div v-if="isLoading && virtualEvents.length === 0" class="loading-state">
        로그를 불러오는 중입니다...
      </div>

      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>

      <div v-else-if="virtualEvents.length === 0" class="empty-events">
        발생한 이벤트가 없습니다.
      </div>

      <div v-else class="stream-wrapper">
        <div class="timeline-line"></div>

        <!-- 💡 핵심 포인트: 리스트 전체를 CSS flex-direction: column-reverse로 뒤집음 -->
        <TransitionGroup 
          tag="ul" 
          name="stream" 
          class="event-list reverse-layout"
        >
          <!-- 
            이제 데이터는 순방향(push)으로 쌓입니다. 기존 아이템들의 index는 고정되므로,
            Vue는 새로 추가된 맨 뒤의 아이템에만 정확하게 진입 애니메이션을 부여합니다.
          -->
          <li 
            v-for="event in virtualEvents" 
            :key="event.event_id" 
            :class="['event-item', event.type.toLowerCase()]"
          >
            <div class="timeline-dot"></div>
            
            <div class="event-card">
              <div class="card-header">
                <span class="event-type">{{ event.type }}</span>
                <span class="event-time">{{ event.time }}</span>
              </div>
              <p class="card-message">{{ event.message }}</p>
            </div>
          </li>
        </TransitionGroup>
      </div>
    </div>

    <div class="footer">
      <button class="download-btn" @click="downloadLogCsv" :disabled="virtualEvents.length === 0">
        DOWNLOAD LOG REPORT (.CSV)
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue';
import { useRobotEvents } from '../composables/useRobotEvents';

const { events, isLoading, error, downloadLogCsv } = useRobotEvents();

const virtualEvents = ref<any[]>([]);
let intervalId: any = null;
let currentRenderedIndex = 0;

const startHydrationLoop = () => {
  if (intervalId) return;

  intervalId = setInterval(async () => {
    const rawEvents = events.value;
    if (!rawEvents || rawEvents.length === 0) return;

    // 1. 최초 로드 처리 (순방향 push 구조이므로 원본 배열 그대로 복사)
    if (virtualEvents.value.length === 0) {
      virtualEvents.value = [...rawEvents];
      currentRenderedIndex = rawEvents.length;
      return;
    }

    // 2. 단일/복수 유입 상관없이 인덱스 기준 순차 펌핑
    if (rawEvents.length > currentRenderedIndex) {
      const nextEventToRender = rawEvents[currentRenderedIndex];
      
      if (nextEventToRender) {
        // 💡 배열의 맨 뒤에 넣습니다. 기존 원소들의 순서가 보존되어 엉뚱한 아래 리스트가 출렁이지 않습니다.
        virtualEvents.value.push(nextEventToRender);
        currentRenderedIndex++; 
        
        await nextTick();
      }
    }
  }, 60); // 부드러운 유입감을 위해 60ms 세팅
};

watch(events, (newVal) => {
  if (newVal && newVal.length > 0) {
    startHydrationLoop();
  }
}, { immediate: true });

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});
</script>

<style scoped>
/* 타입별 메인 테마 색상 */
.info { --theme-color: #bfaee3; --bg-color: #f7f6fc; --text-color: #2b3674; }
.alert { --theme-color: #ff5b5b; --bg-color: #fff5f5; --text-color: #a30000; }
.system { --theme-color: #4a90e2; --bg-color: #f0f7ff; --text-color: #2b3674; }
.warning { --theme-color: #ff9f43; --bg-color: #fff9f3; --text-color: #a35200; }

.card {
  height: 100%;
  padding: 24px 12px; 
  box-sizing: border-box;
  font-family: 'Segoe UI', Arial, sans-serif;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 12px;
  flex-shrink: 0;
}

.title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #a3aed0;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.icon { width: 16px; height: 16px; }

.main-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  padding: 0 4px 0 0;
  width: 100%;
}

.stream-wrapper {
  position: relative;
  padding-left: 28px;
  padding-right: 15px;
}

.timeline-line {
  position: absolute;
  left: 13px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  background-color: #e9edf7;
}

/* 💡 [핵심 스타일] 최신 데이터(배열 끝부분)가 무조건 시각적으로 맨 위로 오도록 레이아웃 반전 */
.event-list.reverse-layout {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column-reverse; /* 아래에 깔리는 원소가 시각적으로 위로 배치됨 */
  gap: 20px;
}

.event-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.timeline-dot {
  position: absolute;
  left: -18px;
  top: 14px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--theme-color);
  z-index: 1;
}

.event-card {
  flex: 1;
  width: 100%;
  background-color: var(--bg-color);
  border-radius: 12px;
  padding: 12px 16px;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.event-type { font-size: 11px; font-weight: 800; color: var(--theme-color); }
.event-time { font-size: 11px; color: #a3aed0; }
.card-message { margin: 0; font-size: 13px; font-weight: 600; color: var(--text-color); line-height: 1.4; }

.loading-state, .error-state, .empty-events {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a3aed0;
  font-size: 14px;
}
.error-state { color: #ff5b5b; }

.footer {
  margin-top: auto;
  padding: 0 12px;
  flex-shrink: 0;
}

.download-btn {
  width: 100%;
  padding: 14px;
  background-color: #f4f7fe;
  border: 1px solid #e9edf7;
  border-radius: 12px;
  color: #a3aed0;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.download-btn:not(:disabled):hover {
  background-color: #e9edf7;
  color: #2b3674;
}
.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.main-content::-webkit-scrollbar { width: 4px; }
.main-content::-webkit-scrollbar-track { background: transparent; }
.main-content::-webkit-scrollbar-thumb { background: #e9edf7; border-radius: 4px; }

/* 💡 레이아웃을 뒤집었기 때문에 새 데이터는 시각적 최상단(실제 코드상 맨 뒤)에서 자연스럽게 내려옵니다. */
.stream-enter-from {
  opacity: 0;
  transform: translateY(-30px);
}
.stream-enter-active {
  transition: 
    opacity 0.25s ease-out, 
    transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
/* 기존 아이템들이 아래로 안정적으로 밀려날 때의 트랜지션 보장 */
.stream-move {
  transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}
</style>