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
      <div v-if="isLoading && events.length === 0" class="loading-state">
        로그를 불러오는 중입니다...
      </div>

      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>

      <div v-else-if="events.length === 0" class="empty-events">
        발생한 이벤트가 없습니다.
      </div>

      <div v-else class="stream-wrapper">
        <div class="timeline-line"></div>

        <ul class="event-list">
          <li 
            v-for="event in events" 
            :key="event.id" 
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
        </ul>
      </div>
    </div>

    <div class="footer">
      <button class="download-btn" @click="downloadLogCsv" :disabled="events.length === 0">
        DOWNLOAD LOG REPORT (.CSV)
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotEvents } from '../composables/useRobotEvents';

const { events, isLoading, error, downloadLogCsv } = useRobotEvents();
</script>

<style scoped>
/* 타입별 메인 테마 색상 */
.info { --theme-color: #bfaee3; --bg-color: #f7f6fc; --text-color: #2b3674; }
.alert { --theme-color: #ff5b5b; --bg-color: #fff5f5; --text-color: #a30000; }
.system { --theme-color: #4a90e2; --bg-color: #f0f7ff; --text-color: #2b3674; }
.warning { --theme-color: #ff9f43; --bg-color: #fff9f3; --text-color: #a35200; }

/* 💡 변경 포인트: 좌우 패딩을 기존 24px -> 12px로 줄여 가로 여백 최소화 */
.card {
  height: 100%;
  padding: 24px 12px; 
  box-sizing: border-box;
  font-family: 'Segoe UI', Arial, sans-serif;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
  display: flex;
  flex-direction: column;
}

/* 헤더 영역도 줄어든 패딩에 맞춰 좌우 여백 정렬(패딩 12px 추가) */
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

/* 💡 변경 포인트: 패딩을 없애고 100% 확장 */
.main-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  padding: 0 4px 0 0; /* 우측 스크롤바 정렬용 미세 여백 */
  width: 100%;
}

/* 타임라인 배치 컨테이너 */
.stream-wrapper {
  position: relative;
  padding-left: 28px; /* 타임라인 선과 왼쪽 끝 정렬 여백 */
  padding-right: 15px; /* 스트림 카드가 우측 벽에 붙지 않도록 미세 여백 */
}

/* 세로 가이드 선 (padding-left 값에 맞춰 좌측 배치 조정) */
.timeline-line {
  position: absolute;
  left: 13px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  background-color: #e9edf7;
}

.event-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.event-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  width: 100%; /* 너비 꽉 차게 */
}

/* 타임라인 왼쪽 점 위치 조정 */
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

/* 💡 변경 포인트: 내부 카드가 가로 공간을 100% 꽉 채우도록 설정 */
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

.loading-state, .error-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a3aed0;
  font-size: 14px;
}
.error-state { color: #ff5b5b; }

/* 이벤트가 없을 때 중앙 메시지 */
.empty-events {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a3aed0;
  font-size: 14px;
}

/* 💡 변경 포인트: 푸터 내부 버튼이 양옆에 약간의 균형 잡힌 여백만 갖도록 조정 */
.footer {
  margin-top: auto;
  padding: 0 12px;
  flex-shrink: 0;
}

.download-btn {
  width: 100%; /* 가로 폭 꽉 채우기 */
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

/* 스크롤바 스타일 유지 */
.main-content::-webkit-scrollbar { width: 4px; }
.main-content::-webkit-scrollbar-track { background: transparent; }
.main-content::-webkit-scrollbar-thumb { background: #e9edf7; border-radius: 4px; }
</style>