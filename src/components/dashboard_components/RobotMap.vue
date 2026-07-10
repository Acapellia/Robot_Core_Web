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

        <button
          class="map-nav-btn left"
          :disabled="mapStore.maps.length <= 1"
          title="이전 맵"
          @click="mapStore.prevMap()"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
        </button>

        <div class="canvas-space" :style="{ transform: `scale(${zoomLevel / 100})` }">

          <div class="map-stage">
            <canvas ref="mapCanvasRef" class="map-canvas" width="400" height="400"></canvas>
          </div>

          <div v-if="mapStore.currentMap" class="map-filename-label">
            {{ mapStore.currentMap.filename }}
          </div>

        </div>

        <button
          class="map-nav-btn right"
          :disabled="mapStore.maps.length <= 1"
          title="다음 맵"
          @click="mapStore.nextMap()"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';
import { useRobotMap } from '../../composables/useRobotMap';
import { useRobotMapStore } from '../../stores/robotMapStore';
import { renderMapToCanvas } from '../../utils/mapCanvasRenderer';

const { mapInfo, zoomLevel, zoomIn, zoomOut } = useRobotMap();
const mapStore = useRobotMapStore();

// 맵 이미지(canvas) 위에 graph_nodes / graph_edges / waypoints를 벡터로 겹쳐 그리는 렌더러
const mapCanvasRef = ref<HTMLCanvasElement | null>(null);

const renderMap = () => {
  const canvas = mapCanvasRef.value;
  if (!canvas) return;
  renderMapToCanvas(canvas, mapStore.currentMap);
};

watch(() => mapStore.currentMap, renderMap);

onMounted(() => {
  mapStore.connectWebSocket();
  renderMap();
});

onUnmounted(() => {
  mapStore.stopMonitoring();
});
</script>

<style scoped>
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

.map-stage {
  width: 90%;
  height: 90%;
  position: relative;
}

/* 맵 이미지 + graph_nodes/graph_edges/waypoints 오버레이를 그리는 캔버스 */
.map-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* 맵 뷰포트 좌우의 작은 맵 전환 화살표 버튼 */
.map-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background-color: #ffffff;
  border: 1px solid rgba(13, 27, 34, 0.2);
  border-radius: 50%;
  color: #707eae;
  cursor: pointer;
  padding: 5px;
  transition: all 0.2s ease;
}
.map-nav-btn.left { left: 10px; }
.map-nav-btn.right { right: 10px; }
.map-nav-btn:hover:not(:disabled) {
  background-color: #e2e8f0;
  color: #1a3ba5;
}
.map-nav-btn:disabled {
  opacity: 0.35;
  cursor: default;
}
.map-nav-btn svg { width: 100%; height: 100%; }

/* 맵 하단의 파일명 라벨 (기존 로봇이름/상태 라벨 위치보다 조금 더 아래쪽) */
.map-filename-label {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 5;
  font-size: 14px;
  font-weight: 700;
  color: #1b2559;
}
</style>