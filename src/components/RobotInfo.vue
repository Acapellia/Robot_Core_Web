<template>
  <div class="robot-info-container card">
    <div v-if="!robotInfo" class="empty-state">
      데이터 수신 대기 중...
    </div>

    <div v-else class="info-content-zone">
      <div class="top-row">
        <div class="meta-left">
          <h2 class="robot-title">
            {{ robotInfo.name }}
          </h2>
          <p class="ip-lbl">IP: {{ robotInfo.ipAddress }}</p>
        </div>

        <div :class="['status-badge', robotInfo.status.toLowerCase()]">
          {{ robotInfo.status }}
        </div>
      </div>

      <div class="battery-section">
        <div class="battery-header">
          <span class="battery-title">Battery</span>
          <span class="battery-value">{{ robotInfo.battery }}%</span>
        </div>
        <div class="battery-track-bar">
          <div class="battery-fill-level" :style="{ width: `${robotInfo.battery}%` }"></div>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-card">
          <span class="metric-label">CURRENT MAP</span>
          <span class="metric-value">{{ robotInfo.currentMap }}</span>
        </div>
        
        <div class="metric-card">
          <span class="metric-label">UPTIME</span>
          <span class="metric-value">{{ robotInfo.uptime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotInfo } from '../composables/UseRobotInfo';

const { robotInfo } = useRobotInfo();
</script>

<style scoped>
.patrolling { --badge-bg: #ffffff; --badge-color: #1a3ba5; }
.idle { --badge-bg: #ff9f43; --badge-color: #ffffff; }
.offline { --badge-bg: #a3aed0; --badge-color: #ffffff; }

/* 💡 가로가 길고 세로가 짧은 컴포넌트 박스 환경 대응 스타일 */
.robot-info-container {
  width: 100%;
  height: 100%;
  padding: 16px 20px; /* 기존 24px 패딩을 줄여 높이 확보 */
  box-sizing: border-box;
  background-color: #e4f2ff; /* 원본의 은은한 라이트 블루 계열 배경 상속 */
  border-radius: 16px;
  font-family: 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 내부 요소들을 세로 정중앙에 밀착 정렬 */
  overflow: hidden; /* 절대 스크롤바가 안 터지도록 가둠 */
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
}

.info-content-zone {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 12px; /* 각 층간 간격을 18px -> 12px로 축소하여 압축 */
}

/* 1층 정렬 */
.top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.robot-title {
  margin: 0;
  font-size: 22px; /* 폰트 스케일 다운 */
  font-weight: 800;
  color: #1b2559;
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.version-lbl {
  font-size: 11px;
  font-weight: 500;
  color: #707eae;
}

.ip-lbl {
  margin: 2px 0 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #707eae;
}

/* 상태 배지 */
.status-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.3px;
  background-color: var(--badge-bg);
  color: var(--badge-color);
}

/* 2층 배터리 트랙바 */
.battery-section {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 4px;
}

.battery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.battery-title {
  font-size: 12px;
  font-weight: 700;
  color: #1b2559;
}

.battery-value {
  font-size: 12px;
  font-weight: 700;
  color: #1b2559;
}

.battery-track-bar {
  width: 100%;
  height: 6px; /* 높이를 슬림하게 조절 */
  background-color: rgba(255, 255, 255, 0.5);
  border-radius: 3px;
  overflow: hidden;
}

.battery-fill-level {
  height: 100%;
  background-color: #05cd99;
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* 3층 메트릭 하단 인셋 레이아웃 */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.metric-card {
  background-color: rgba(255, 255, 255, 0.6);
  padding: 8px 12px; /* 위아래 내부 패딩을 좁혀서 납작하게 변형 */
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-label {
  font-size: 10px;
  font-weight: 700;
  color: #a3aed0;
}

.metric-value {
  font-size: 13px;
  font-weight: 700;
  color: #1a3ba5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* 글자가 늘어날 때 깨짐 방지 안전장치 */
}

.empty-state {
  font-size: 12px;
  color: #707eae;
  text-align: center;
}
</style>