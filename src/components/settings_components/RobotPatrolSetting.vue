<template>
  <div class="robot-patrol-setting">
    <div class="header">
      <h3 class="title">
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
          <line x1="8" y1="2" x2="8" y2="18"></line>
          <line x1="16" y1="6" x2="16" y2="22"></line>
        </svg>
        {{ mapStore.currentMap?.filename ?? 'PATROL SETTING' }}
      </h3>
    </div>

    <div class="body">
      <div class="map-column">
        <div class="spatial-viewport" ref="spatialViewportRef">
          <button class="map-nav-btn left" :disabled="mapStore.maps.length <= 1" title="이전 맵" @click="mapStore.prevMap()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>

          <div class="canvas-space" :style="canvasSpaceStyle">
            <div class="map-stage">
              <canvas
                ref="mapCanvasRef"
                class="map-canvas"
                :class="{ addable: addMode }"
                width="400"
                height="400"
                @click="handleCanvasClick"
                @pointerdown="onPointerDown"
                @pointermove="onPointerMove"
                @pointerup="onPointerUp"
                @pointercancel="onPointerUp"
              ></canvas>
            </div>
          </div>

          <button class="map-nav-btn right" :disabled="mapStore.maps.length <= 1" title="다음 맵" @click="mapStore.nextMap()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>

          <div v-if="zoomLevel > 100" class="minimap">
            <canvas ref="minimapCanvasRef" class="minimap-canvas" width="400" height="400"></canvas>
            <div
              class="minimap-viewport-rect"
              :style="{ left: minimapRect.left + '%', top: minimapRect.top + '%', width: minimapRect.width + '%', height: minimapRect.height + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <div class="sidebar-column">
        <div class="sidebar-controls">
          <button class="zoom-btn" @click="zoomIn" title="확대">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          </button>
          <button class="zoom-btn" @click="zoomOut" title="축소">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          </button>
          <button
            class="add-mode-btn"
            :class="{ active: addMode }"
            :disabled="!mapStore.currentMap?.image_transform"
            @click="toggleAddMode"
          >
            {{ addMode ? '추가 중...' : '웨이포인트 추가' }}
          </button>
        </div>

        <div class="waypoint-box">
          <h4 class="panel-title">WAYPOINTS ({{ draftWaypoints.length }})</h4>

          <div v-if="draftWaypoints.length === 0" class="empty-hint">
            "웨이포인트 추가"를 누른 뒤 지도를 클릭해 경로를 그려주세요.
          </div>

          <div v-else class="waypoint-list">
            <div v-for="(p, i) in draftWaypoints" :key="i" class="waypoint-row">
              <span class="wp-index">{{ i + 1 }}</span>
              <span class="wp-coord">x {{ p.x.toFixed(2) }}, y {{ p.y.toFixed(2) }}</span>
              <div class="wp-actions">
                <button class="wp-btn" :disabled="i === 0" @click="moveWaypoint(i, -1)" title="위로">▲</button>
                <button class="wp-btn" :disabled="i === draftWaypoints.length - 1" @click="moveWaypoint(i, 1)" title="아래로">▼</button>
                <button class="wp-btn danger" @click="removeWaypoint(i)" title="삭제">×</button>
              </div>
            </div>
          </div>

          <div class="footer-actions">
            <button class="reset-btn" :disabled="draftWaypoints.length === 0" @click="resetDraft">초기화</button>
            <button class="save-btn" :disabled="draftWaypoints.length === 0" @click="saveWaypoints">저장</button>
          </div>

          <p v-if="saveMessage" class="save-message" :class="saveState">{{ saveMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRobotMap } from '../../composables/useRobotMap';
import { useRobotMapStore } from '../../stores/robotMapStore';
import { useRobotStore } from '../../stores/robotStore';
import { useHubStore } from '../../stores/hubStore';
import { renderMapToCanvas, toWaypoints, type WaypointPoint } from '../../utils/mapCanvasRenderer';
import { computeCanvasFit, worldToCanvas, canvasToWorld, type CanvasFit } from '../../utils/mapTransform';

const { zoomLevel, zoomIn, zoomOut } = useRobotMap();
const mapStore = useRobotMapStore();
const robotStore = useRobotStore();
const hubStore = useHubStore();
const { hubs, selectedHubId } = storeToRefs(hubStore);

// HubManagement(RobotCoreSetting.vue)에서 선택된 허브(로봇)에 맞춰 표시할 맵을 결정한다
const selectedHubSource = computed(() => {
  const hub = hubs.value.find((h) => h.ip === selectedHubId.value);
  return hub ? `hub_${hub.ip}_${hub.port}` : null;
});
watch(selectedHubSource, (source) => mapStore.setActiveSource(source), { immediate: true });

const spatialViewportRef = ref<HTMLDivElement | null>(null);
const mapCanvasRef = ref<HTMLCanvasElement | null>(null);
const minimapCanvasRef = ref<HTMLCanvasElement | null>(null);

const addMode = ref(false);
const draftWaypoints = ref<WaypointPoint[]>([]);
const saveState = ref<'idle' | 'error'>('idle');
const saveMessage = ref('');

// 지도 뷰포트(정사각형) 크기. 컨테이너 크기에 맞춰 ResizeObserver로 갱신된다.
const viewportSquareSize = ref(280);
// 확대 시 옆으로 드래그 이동한 오프셋 (CSS px, transform 순서상 scale의 영향을 받지 않는다)
const panX = ref(0);
const panY = ref(0);
const minimapRect = ref({ left: 0, top: 0, width: 100, height: 100 });

const canvasSpaceStyle = computed(() => ({
  width: `${viewportSquareSize.value}px`,
  height: `${viewportSquareSize.value}px`,
  transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomLevel.value / 100})`
}));

let resizeObserver: ResizeObserver | null = null;
let dragState: { startX: number; startY: number; originX: number; originY: number; dragging: boolean } | null = null;
let justDragged = false;

function clamp01(v: number) {
  return Math.min(1, Math.max(0, v));
}

// 확대된 상태에서 팬 오프셋이 지도 바깥으로 완전히 벗어나지 않도록 제한
function applyPan(nx: number, ny: number) {
  const viewport = spatialViewportRef.value;
  if (!viewport) return;
  const scale = zoomLevel.value / 100;
  const scaledSize = viewportSquareSize.value * scale;
  const maxPanX = Math.max(0, (scaledSize - viewport.clientWidth) / 2);
  const maxPanY = Math.max(0, (scaledSize - viewport.clientHeight) / 2);
  panX.value = Math.min(maxPanX, Math.max(-maxPanX, nx));
  panY.value = Math.min(maxPanY, Math.max(-maxPanY, ny));
  updateMinimapRect();
}

// 미니맵 위에 표시할 "현재 보이는 영역" 사각형을 팬/줌 값으로부터 계산 (전체 지도 대비 비율, %)
function updateMinimapRect() {
  const viewport = spatialViewportRef.value;
  if (!viewport || viewportSquareSize.value === 0) return;
  const scale = zoomLevel.value / 100;
  const cw = viewportSquareSize.value;

  const fracW = clamp01((viewport.clientWidth / scale) / cw);
  const fracH = clamp01((viewport.clientHeight / scale) / cw);
  const fracCenterX = 0.5 - (panX.value / scale) / cw;
  const fracCenterY = 0.5 - (panY.value / scale) / cw;
  const left = clamp01(fracCenterX - fracW / 2);
  const top = clamp01(fracCenterY - fracH / 2);

  minimapRect.value = {
    left: left * 100,
    top: top * 100,
    width: Math.min(fracW, 1 - left) * 100,
    height: Math.min(fracH, 1 - top) * 100
  };
}

function updateViewportSquareSize() {
  const el = spatialViewportRef.value;
  if (!el) return;
  const size = Math.max(160, Math.min(el.clientWidth, el.clientHeight) - 20);
  if (size !== viewportSquareSize.value) {
    viewportSquareSize.value = size;
    applyPan(panX.value, panY.value);
  }
}

function loadDraftFromCurrentMap() {
  draftWaypoints.value = toWaypoints(mapStore.currentMap?.waypoints).map((p) => ({ ...p }));
  saveState.value = 'idle';
  saveMessage.value = '';
}

function drawDraftOverlayOn(canvas: HTMLCanvasElement, fit: CanvasFit | null) {
  const map = mapStore.currentMap;
  const ctx = canvas.getContext('2d');
  const transform = map?.image_transform;
  if (!ctx || !map || !transform || !fit || draftWaypoints.value.length === 0) return;

  const toCanvasPoint = (x: number, y: number) => worldToCanvas(x, y, transform, fit);

  if (draftWaypoints.value.length > 1) {
    ctx.beginPath();
    draftWaypoints.value.forEach((p, i) => {
      const { cx, cy } = toCanvasPoint(p.x, p.y);
      if (i === 0) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    });
    ctx.strokeStyle = '#2f6fed';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  draftWaypoints.value.forEach((p, i) => {
    const { cx, cy } = toCanvasPoint(p.x, p.y);
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#2f6fed';
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(i + 1), cx, cy);
  });
}

function renderAll() {
  const canvas = mapCanvasRef.value;
  if (canvas) renderMapToCanvas(canvas, mapStore.currentMap, (fit) => drawDraftOverlayOn(canvas, fit));

  const mini = minimapCanvasRef.value;
  if (mini) renderMapToCanvas(mini, mapStore.currentMap, (fit) => drawDraftOverlayOn(mini, fit));

  updateMinimapRect();
}

function toggleAddMode() {
  addMode.value = !addMode.value;
}

function onPointerDown(evt: PointerEvent) {
  if (zoomLevel.value <= 100) return; // 확대 상태가 아니면 이동할 여지가 없음
  dragState = { startX: evt.clientX, startY: evt.clientY, originX: panX.value, originY: panY.value, dragging: false };
  (evt.currentTarget as HTMLElement).setPointerCapture(evt.pointerId);
}

function onPointerMove(evt: PointerEvent) {
  if (!dragState) return;
  const dx = evt.clientX - dragState.startX;
  const dy = evt.clientY - dragState.startY;
  if (!dragState.dragging && Math.hypot(dx, dy) > 4) dragState.dragging = true;
  if (!dragState.dragging) return;
  applyPan(dragState.originX + dx, dragState.originY + dy);
}

function onPointerUp() {
  if (dragState?.dragging) justDragged = true;
  dragState = null;
}

function handleCanvasClick(evt: MouseEvent) {
  if (justDragged) {
    justDragged = false;
    return;
  }
  if (!addMode.value) return;
  const canvas = mapCanvasRef.value;
  const transform = mapStore.currentMap?.image_transform;
  if (!canvas || !transform) return;

  const rect = canvas.getBoundingClientRect();
  const cx = (evt.clientX - rect.left) * (canvas.width / rect.width);
  const cy = (evt.clientY - rect.top) * (canvas.height / rect.height);
  const fit = computeCanvasFit(transform, canvas.width);
  const { x, y } = canvasToWorld(cx, cy, transform, fit);

  draftWaypoints.value = [...draftWaypoints.value, { x, y }];
}

function removeWaypoint(index: number) {
  draftWaypoints.value = draftWaypoints.value.filter((_, i) => i !== index);
}

function moveWaypoint(index: number, dir: -1 | 1) {
  const target = index + dir;
  if (target < 0 || target >= draftWaypoints.value.length) return;
  const next = [...draftWaypoints.value];
  [next[index], next[target]] = [next[target], next[index]];
  draftWaypoints.value = next;
}

function resetDraft() {
  loadDraftFromCurrentMap();
}

function saveWaypoints() {
  const map = mapStore.currentMap;
  if (!map || !map.image_transform) {
    saveState.value = 'error';
    saveMessage.value = '맵 데이터를 아직 수신하지 못했습니다.';
    return;
  }

  const robotId = robotStore.robots.find((r) => r.hubSource === selectedHubSource.value)?.id ?? null;

  const sent = hubStore.sendControlMessage({
    type: 'set_patrol_route',
    robot_id: robotId,
    map_filename: map.filename,
    frame_id: map.frame_id,
    // z=0: 탑뷰로 평탄화된 평면 기준이라 순찰 경로 높이는 바닥면(0)으로 고정한다
    waypoints: draftWaypoints.value.map((p) => ({ x: p.x, y: p.y, z: 0 }))
  });

  if (sent) {
    mapStore.setWaypointsForCurrentMap(draftWaypoints.value);
    saveState.value = 'idle';
    saveMessage.value = '';
  } else {
    saveState.value = 'error';
    saveMessage.value = '허브 연결이 끊어져 있어 전송하지 못했습니다.';
  }
}

watch(() => mapStore.currentMap?.filename, () => {
  panX.value = 0;
  panY.value = 0;
  loadDraftFromCurrentMap();
});
watch(() => mapStore.currentMap, renderAll);
watch(draftWaypoints, renderAll, { deep: true });
watch(zoomLevel, (val) => {
  if (val <= 100) {
    panX.value = 0;
    panY.value = 0;
  } else {
    applyPan(panX.value, panY.value);
  }
}, { flush: 'post' });

onMounted(() => {
  mapStore.connectWebSocket();
  loadDraftFromCurrentMap();

  updateViewportSquareSize();
  if (spatialViewportRef.value) {
    resizeObserver = new ResizeObserver(() => updateViewportSquareSize());
    resizeObserver.observe(spatialViewportRef.value);
  }

  renderAll();
});

onUnmounted(() => {
  resizeObserver?.disconnect();
  mapStore.stopMonitoring();
});
</script>

<style scoped>
.robot-patrol-setting {
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: 24px;
  box-sizing: border-box;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
  font-family: 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

.header {
  flex-shrink: 0;
  margin-bottom: 16px;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.header-icon { width: 16px; height: 16px; flex-shrink: 0; }

.body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 16px;
}

/* 지도 : 웨이포인트 사이드바 = 8 : 2 고정 비율 (고정 px 값이 아니라 항상 이 비율을 유지) */
.map-column {
  flex: 8 1 0;
  min-width: 0;
  min-height: 0;
  display: flex;
}

.spatial-viewport {
  width: 100%;
  height: 100%;
  background-color: #f8fafc;
  border-radius: 14px;
  border: 1px solid rgba(13, 27, 34, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.canvas-space {
  position: relative;
  transition: width 0.15s ease, height 0.15s ease;
}

.map-stage { width: 100%; height: 100%; position: relative; }

.map-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  touch-action: none;
}
.map-canvas.addable { cursor: crosshair; }

.map-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background-color: #ffffff;
  border: 1px solid rgba(13, 27, 34, 0.2);
  border-radius: 50%;
  color: #707eae;
  cursor: pointer;
  padding: 6px;
}
.map-nav-btn.left { left: 14px; }
.map-nav-btn.right { right: 14px; }
.map-nav-btn:hover:not(:disabled) { background-color: #e2e8f0; color: #1a3ba5; }
.map-nav-btn:disabled { opacity: 0.35; cursor: default; }
.map-nav-btn svg { width: 100%; height: 100%; }

.minimap {
  position: absolute;
  right: 14px;
  bottom: 14px;
  width: 96px;
  height: 96px;
  border-radius: 10px;
  border: 1px solid rgba(13, 27, 34, 0.35);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(13, 27, 34, 0.25);
  z-index: 20;
}
.minimap-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: #ffffff;
}
.minimap-viewport-rect {
  position: absolute;
  border: 1.5px solid #2f6fed;
  background: rgba(47, 111, 237, 0.15);
  pointer-events: none;
}

/* 사이드바: 확대/추가 버튼 + 웨이포인트 박스 (지도와 항상 2 : 8 비율) */
.sidebar-column {
  flex: 2 1 0;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-controls {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}

.zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f4f7fe;
  border: 1px solid rgba(13, 27, 34, 0.2);
  border-radius: 10px;
  color: #707eae;
  cursor: pointer;
  padding: 6px;
  flex-shrink: 0;
}
.zoom-btn:hover { background-color: #e2e8f0; color: #1a3ba5; }
.zoom-btn svg { width: 100%; height: 100%; }

.add-mode-btn {
  flex: 1;
  height: 32px;
  padding: 0 10px;
  background-color: #f4f7fe;
  border: 1px solid rgba(13, 27, 34, 0.2);
  border-radius: 10px;
  color: #707eae;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  line-height: 1.2;
}
.add-mode-btn:hover:not(:disabled) { background-color: #e2e8f0; color: #1a3ba5; }
.add-mode-btn.active { background-color: #2f6fed; border-color: #2f6fed; color: #ffffff; }
.add-mode-btn:disabled { opacity: 0.4; cursor: default; }

/* 웨이포인트 구역: 별도 박스로 구분, 남는 세로 공간을 대부분 차지 */
.waypoint-box {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  background: #f8faff;
  border: 1px solid rgba(13, 27, 34, 0.2);
  border-radius: 14px;
  box-sizing: border-box;
}

.panel-title {
  margin: 0;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: #a3aed0;
  letter-spacing: 0.5px;
}

.empty-hint {
  font-size: 12px;
  color: #a3aed0;
  padding: 10px 0;
}

.waypoint-list {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  padding-right: 4px;
}

.waypoint-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border: 1px solid #e9edf7;
  border-radius: 10px;
  background: #ffffff;
  flex-shrink: 0;
}

.wp-index {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2f6fed;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wp-coord {
  flex: 1;
  font-size: 12px;
  color: #2b3674;
}

.wp-actions { display: flex; gap: 4px; }

.wp-btn {
  width: 22px;
  height: 22px;
  border: 1px solid #e0e5f2;
  border-radius: 6px;
  background: #ffffff;
  color: #707eae;
  font-size: 11px;
  cursor: pointer;
}
.wp-btn:hover:not(:disabled) { background-color: #e2e8f0; }
.wp-btn:disabled { opacity: 0.35; cursor: default; }
.wp-btn.danger { color: #e0455f; }
.wp-btn.danger:hover { background-color: #fde8ea; }

.footer-actions {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.reset-btn, .save-btn {
  height: 34px;
  padding: 0 16px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid rgba(13, 27, 34, 0.2);
}
.reset-btn { background: #f4f7fe; color: #707eae; }
.reset-btn:hover:not(:disabled) { background-color: #e2e8f0; }
.reset-btn:disabled, .save-btn:disabled { opacity: 0.4; cursor: default; }
.save-btn { background: #2f6fed; color: #ffffff; border-color: #2f6fed; }
.save-btn:hover:not(:disabled) { background: #2559c9; }

.save-message { margin: 0; flex-shrink: 0; font-size: 12px; font-weight: 600; text-align: right; }
.save-message.error { color: #e0455f; }
</style>
