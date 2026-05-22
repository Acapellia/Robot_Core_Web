<template>
  <div class="robot-map card">
    <div class="header">
      <h3 class="title">
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
          <line x1="8" y1="2" x2="8" y2="18"></line>
          <line x1="16" y1="6" x2="16" y2="22"></line>
        </svg>
        {{ mapInfo?.mapName }}
      </h3>

      <div class="zoom-controls">
        <button class="zoom-btn" @click="zoomIn" title="확대">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <button class="zoom-btn" @click="zoomOut" title="축소">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
    </div>

    <div class="body">
      <div class="spatial-viewport">
        
        <div class="canvas-space" :style="{ transform: `scale(${zoomLevel / 100})` }">
          
          <svg class="map-vector-layer" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            
            <g class="wall-lines">
              <rect x="50" y="50" width="300" height="300" rx="12" fill="none" stroke="#d2c5f1" stroke-width="2.5" />
              <line x1="50" y1="130" x2="232" y2="130" stroke="#d2c5f1" stroke-width="2" />
              <line x1="232" y1="50" x2="232" y2="210" stroke="#d2c5f1" stroke-width="2" />
            </g>

            <g v-if="mapInfo && mapInfo.patrolPath.length > 0">
              <polyline 
                :points="mapInfo.patrolPath.map(p => `${(p.x * 400)/100},${(p.y * 400)/100}`).join(' ')"
                fill="none" 
                stroke="#b2b8db" 
                stroke-width="3" 
                stroke-dasharray="6, 6" 
                stroke-linecap="round"
              />
              <circle cx="100" cy="80" r="4" fill="#b2b8db" />
              <circle cx="300" cy="304" r="4" fill="#b2b8db" />
            </g>

            <g v-if="mapInfo" class="robot-marker" :style="markerStyle">
              <circle cx="0" cy="0" r="16" fill="#1a3ba5" fill-opacity="0.15" />
              <circle cx="0" cy="0" r="11" fill="#4250ab" />
              <circle cx="0" cy="0" r="4" fill="#ffffff" />
            </g>
          </svg>

          <div v-if="mapInfo" class="live-robot-label">
            <h4 class="label-name">{{ mapInfo.robotName }}</h4>
            <div :class="['label-status', mapInfo.robotStatus.toLowerCase()]">
              <span class="status-dot"></span>
              {{ mapInfo.robotStatus }}
            </div>
          </div>

        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRobotMap } from '../../composables/useRobotMap';

const { mapInfo, zoomLevel, zoomIn, zoomOut } = useRobotMap();

// API 실시간 백분율(%) 좌표를 SVG 상 절대 픽셀(400px 가로세로 기준)로 파싱하는 스타일 바인딩 계산
const markerStyle = computed(() => {
  if (!mapInfo.value) return {};
  const pixelX = (mapInfo.value.robotPosition.x * 400) / 100;
  const pixelY = (mapInfo.value.robotPosition.y * 400) / 100;
  return {
    transform: `translate(${pixelX}px, ${pixelY}px)`
  };
});
</script>

<style scoped>
/* 로봇 관제 상태별 컬러 스펙 */
.patrolling { --status-color: #05cd99; }
.idle { --status-color: #ff9f43; }
.offline { --status-color: #a3aed0; }

/* 💡 카드 레이아웃 정밀 고정 및 가로 정렬 */
.robot-map {
  width: 100%;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
  font-family: 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between; /* 타이틀 좌측, 줌 버튼 우측 분할 */
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
  width: 100%;
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
  text-transform: uppercase;
}
.header-icon { width: 16px; height: 16px; }

/* 이미지의 상단 + / - 컨트롤 패널 스타일 스펙 동기화 */
.zoom-controls {
  display: flex;
  gap: 6px;
}

.zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background-color: #f4f7fe;
  border: none;
  border-radius: 6px;
  color: #707eae;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
}
.zoom-btn:hover {
  background-color: #e2e8f0;
  color: #1a3ba5;
}
.zoom-btn svg { width: 100%; height: 100%; }

/* 본문 도화지 뷰포트 영역 */
.body {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
}

/* 이미지 속 소프트 블루그레이 백그라운드 매칭 */
.spatial-viewport {
  width: 100%;
  height: 100%;
  background-color: #f8fafc;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

/* 줌 배율 처리를 격리 수행하는 캔버스 공간 */
.canvas-space {
  width: 100%;
  height: 100%;
  max-width: 420px;
  max-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 벡터 그래픽 레이어 */
.map-vector-layer {
  width: 90%;
  height: 90%;
  overflow: visible;
}

/* 실시간 로봇 위치 마커 좌표 전환 부드러운 애니메이션 선언 */
.robot-marker {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 💡 하단 로봇 네임텍 정보 오버레이 레이아웃 스타일 */
.live-robot-label {
  position: absolute;
  bottom: 45px;
  text-align: center;
  z-index: 5;
}

.label-name {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 700;
  color: #1b2559;
}

.label-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--status-color);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--status-color);
}
</style>