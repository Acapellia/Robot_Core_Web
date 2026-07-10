<template>
  <div class="robot-info-container card">
    <div v-if="!robotInfo" class="empty-state">
      데이터 수신 대기 중...
    </div>

    <div v-else class="info-content-zone">
      <div class="top-row">
        <div class="meta-left">
          <h2 class="robot-title">
            {{ robotInfo.id }}
          </h2>
          <p class="ip-lbl">IP: {{ robotInfo.robot_ip }}</p>
        </div>

        <div :class="['status-badge', robotInfo.statusLabel.toLowerCase()]">
          {{ robotInfo.statusLabel }}
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
          <span class="metric-label">MODE</span>
          <span class="metric-value">{{ robotInfo.mode }}</span>
        </div>

        <div class="metric-card">
          <span class="metric-label">VOICE</span>
          <span class="metric-value">{{ robotInfo.voiceOn ? 'ON' : 'OFF' }}</span>
        </div>

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
import { useRobotInfo } from '../../composables/useRobotInfo';

const { robotInfo } = useRobotInfo();
</script>

<style scoped>
/* robotstatus.statecode 라벨별 배지 색상 */
.unknown { --badge-bg: #a3aed0; --badge-color: #ffffff; }
.poweredoff { --badge-bg: #707eae; --badge-color: #ffffff; }
.initializing { --badge-bg: #4318ff; --badge-color: #ffffff; }
.idle { --badge-bg: #ff9f43; --badge-color: #ffffff; }
.sitting { --badge-bg: #a3aed0; --badge-color: #ffffff; }
.standing { --badge-bg: #2b3674; --badge-color: #ffffff; }
.moving { --badge-bg: #05cd99; --badge-color: #ffffff; }
.recovering { --badge-bg: #ffce20; --badge-color: #1b2559; }
.error { --badge-bg: #e31a1a; --badge-color: #ffffff; }

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
  margin-bottom: 10px;
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
  padding: 5px 20px;
  border-radius: 6px;
  font-size: 12px;
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
  gap: 5px;
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
  column-gap: 8px;
  row-gap: 12px; /* 항목 간 시인성을 위해 세로 간격을 더 확보 */
  width: 100%;
  margin-top: 6px; /* 배터리 영역과의 간격 추가 확보 */
}

.metric-card {
  background-color: rgba(255, 255, 255, 0.6);
  padding: 9px 14px;
  border-radius: 8px;
  display: flex;
  flex-direction: row; /* 종류(라벨)는 왼쪽, 값은 오른쪽에 배치 */
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 30px;
  box-sizing: border-box;
}

.metric-label {
  font-size: 11px;
  font-weight: 700;
  color: #a3aed0;
  flex-shrink: 0;
}

.metric-value {
  font-size: 14px;
  font-weight: 700;
  color: #1a3ba5;
  text-align: right;
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