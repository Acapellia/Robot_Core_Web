<template>
  <div class="messages-container">
    <div v-if="latestAlert" :class="['alert-bar', (latestAlert.type || '').toLowerCase()]">
      
      <div class="icon-wrapper">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
      </div>

      <div class="message-content" :title="latestAlert.message">
        {{ latestAlert.message }}
      </div>

      <div class="time-stamp">
        {{ latestAlert.time }}
      </div>
    </div>

    <div v-else class="empty-state">
      새로운 로봇 메시지나 로그가 없습니다.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLatestAlert } from '../composables/useLatestMessage';

const { latestAlert } = useLatestAlert();
</script>

<style scoped>
/* 💡 핵심 변경 포인트 1: 
  부모 컴포넌트에 걸려있는 흰색 여백(Padding)을 완전히 무시하고 
  사방으로 덮어버리기 위해 마이너스 마진 및 크기 재계산을 적용합니다.
*/
.messages-container {
  /* 부모 `.card`의 padding(12px)을 상쇄하여 흰색 여백을 덮음 */
  margin: -12px;
  width: calc(100% + 24px);
  height: calc(100% + 24px);
  box-sizing: border-box;
  font-family: 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;          /* 컴포넌트 외부로의 스크롤 및 흰 여백 방지 */
  display: flex;
  align-items: stretch;
  border-radius: 8px;       /* 조금 더 둥글게 */
}

/* 💡 핵심 변경 포인트 2: 
  외곽 테두리(Border)를 없애고 부모 카드의 라운딩 각도와 일치시킵니다.
  세로축도 stretch 상태로 가득 채웁니다.
*/
.alert-bar {
  display: flex;
  align-items: center;
  width: 100%;
  height: 100%;
  /* 내부 여백은 유지하되, 배경이 컨테이너 끝까지 닿도록 border-radius는 0으로 둠 */
  padding: 12px;
  box-sizing: border-box;
  background-color: #f3eef9;
  border: 1px solid #b99cff; /* 얇은 진한 보라 테두리 */
  border-radius: 8px;       /* 컨테이너와 동일하게 조금 더 둥글게 */
  overflow: hidden;
}

/* 타입별 스타일 오버라이드 */
.alert-bar.info {
  background-color: #f7f6fc;
  border-color: #bfaee3;
  color: #2b3674;
}
.alert-bar.alert {
  background-color: #fff5f5;
  border-color: #ff5b5b;
  color: #a30000;
}
.alert-bar.system {
  background-color: #f0f7ff;
  border-color: #4a90e2;
  color: #2b3674;
}
.alert-bar.warning {
  background-color: #fff9f3;
  border-color: #ff9f43;
  color: #a35200;
}

.alert-bar.info .alert-icon { color: #bfaee3; }
.alert-bar.alert .alert-icon { color: #ff5b5b; }
.alert-bar.system .alert-icon { color: #4a90e2; }
.alert-bar.warning .alert-icon { color: #ff9f43; }

.alert-bar.info .message-content, .alert-bar.info .time-stamp { color: #2b3674; }
.alert-bar.alert .message-content, .alert-bar.alert .time-stamp { color: #a30000; }
.alert-bar.system .message-content, .alert-bar.system .time-stamp { color: #2b3674; }
.alert-bar.warning .message-content, .alert-bar.warning .time-stamp { color: #a35200; }

/* 동그라미 백그라운드 구역 */
.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background-color: #ffffff;
  border-radius: 50%;
  flex-shrink: 0;           /* 화면이 줄어들어도 정원 유지 */
  margin-right: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 원 안의 느낌표 (!) 크기와 진블루 컬러 고정 */
.alert-icon {
  width: 16px;
  height: 16px;
  color: #1a3ba5;
}

/* 텍스트 영역 */
.message-content {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #1a3ba5;
  letter-spacing: -0.2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 우측 타임스탬프 */
.time-stamp {
  font-size: 13px;
  font-weight: 500;
  color: #a3aed0;
  margin-left: 16px;
  flex-shrink: 0;
}

/* 데이터가 없을 때의 화면도 부모 영역을 가득 채우도록 스타일 일치 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #b99cff;
  background-color: #f4f7fe;
  border: none;
  color: #a3aed0;
  font-size: 14px;
  font-weight: 500;
  box-sizing: border-box;
}
</style>