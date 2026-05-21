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

        <TransitionGroup 
          tag="ul" 
          name="island-pure" 
          class="event-list reverse-layout"
        >
          <li 
            v-for="event in virtualEvents" 
            :key="event.event_id" 
            :class="['event-item', event.type.toLowerCase()]"
          >
            <div class="timeline-dot"></div>
            
            <div class="event-card">
              <div class="card-content-wrapper">
                <div class="card-header">
                  <span class="event-type">{{ event.type }}</span>
                  <span class="event-time">{{ event.time }}</span>
                </div>
                <p class="card-message">{{ event.message }}</p>
              </div>
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

    if (virtualEvents.value.length === 0) {
      virtualEvents.value = [...rawEvents];
      currentRenderedIndex = rawEvents.length;
      return;
    }

    if (rawEvents.length > currentRenderedIndex) {
      const nextEventToRender = rawEvents[currentRenderedIndex];
      
      if (nextEventToRender) {
        virtualEvents.value.push(nextEventToRender);
        currentRenderedIndex++; 
        
        await nextTick();
      }
    }
  }, 60);
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
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.12);
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

.event-list.reverse-layout {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column-reverse; 
  gap: 12px;
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
  top: 16px;
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
  border-radius: 16px;
  padding: 12px 18px;
  box-sizing: border-box;
  overflow: hidden;
}

.card-content-wrapper {
  width: 100%;
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


/* ==========================================================================
   🍏 [Pure Island] 오직 순수한 물리 탄성(Spring)만 남긴 UI 무브먼트
   ========================================================================== */

/* 1. 시작 진입점: 그림자나 하이라이트 효과 없이, 순수하게 쪼그라든 캡슐 상태 */
.island-pure-enter-from {
  opacity: 0;
}

.island-pure-enter-from .event-card {
  transform-origin: 0% 20%; /* 왼쪽 도트 위치 기준 */
  /* 가로는 0에 가깝게, 세로는 납작하게 수축 */
  transform: scale(0.02, 0.1); 
  border-radius: 100px;
}

.island-pure-enter-from .card-content-wrapper {
  opacity: 0;
}

/* 2. 애니메이션 활성화: 애플 하드웨어 특유의 묵직하고 쫀득한 베지에 곡선 적용 */
.island-pure-enter-active {
  transition: opacity 0.1s ease-out;
}

/* 캡슐이 본래 카드로 쫘악 펼쳐지며 끝에 통~ 하고 튕기는 순수 형태 변형 */
.island-pure-enter-active .event-card {
  /* 💡 인위적인 keyframe 애니메이션 전면 삭제. 
     순수하게 cubic-bezier 탄성값으로만 쫀득한 팽창감을 유도 */
  transition: 
    transform 0.48s cubic-bezier(0.175, 0.885, 0.32, 1.25), 
    border-radius 0.35s ease-out;
}

/* 형태가 다 잡히면 글자가 깔끔하게 안착 */
.island-pure-enter-active .card-content-wrapper {
  transition: opacity 0.2s ease-out 0.12s;
}

/* 3. 아래 리스트들이 관성적으로 부드럽게 밀려 내려가는 모션 */
.island-pure-move {
  transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>