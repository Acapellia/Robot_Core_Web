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
import { useRobotMapStore, type RobotMapItem } from '../../stores/robotMapStore';
import { computeCanvasFit, worldToCanvas, type CanvasFit } from '../../utils/mapTransform';

const { mapInfo, zoomLevel, zoomIn, zoomOut } = useRobotMap();
const mapStore = useRobotMapStore();

// 맵 이미지(canvas) 위에 graph_nodes / graph_edges / waypoints를 벡터로 겹쳐 그리는 렌더러
const mapCanvasRef = ref<HTMLCanvasElement | null>(null);

interface GraphNode { id: string | number; x: number; y: number; }
interface GraphEdge { from: string | number; to: string | number; }
interface WaypointPoint { x: number; y: number; }

// 백엔드가 배열([{...}]) 또는 스펙 문서의 객체 맵({Node1:{...}}) 형태 중 무엇을 보내도 처리하도록 정규화
function toNodes(raw: unknown): GraphNode[] {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : Object.values(raw as Record<string, unknown>);
  return list
    .map((n): GraphNode => {
      const node = n as Record<string, unknown>;
      return {
        id: (node.id ?? node.Id ?? node.ID) as string | number,
        x: Number(node.x ?? node.X),
        y: Number(node.y ?? node.Y)
      };
    })
    .filter((n) => Number.isFinite(n.x) && Number.isFinite(n.y));
}

function toEdges(raw: unknown): GraphEdge[] {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : Object.values(raw as Record<string, unknown>);
  return list
    .map((e): GraphEdge => {
      const edge = e as Record<string, unknown>;
      return {
        from: (edge.from ?? edge.From_Node ?? edge.from_node) as string | number,
        to: (edge.to ?? edge.To_Node ?? edge.to_node) as string | number
      };
    })
    .filter((e) => e.from !== undefined && e.to !== undefined);
}

function toWaypoints(raw: unknown): WaypointPoint[] {
  if (!raw) return [];
  if (typeof raw === 'string') {
    const nums = raw.split(',').map((s) => Number(s.trim())).filter((n) => Number.isFinite(n));
    const points: WaypointPoint[] = [];
    for (let i = 0; i + 1 < nums.length; i += 2) points.push({ x: nums[i], y: nums[i + 1] });
    return points;
  }
  const list = Array.isArray(raw) ? raw : Object.values(raw as Record<string, unknown>);
  return list
    .map((w): WaypointPoint => {
      if (Array.isArray(w)) return { x: Number(w[0]), y: Number(w[1]) };
      const point = w as Record<string, unknown>;
      return { x: Number(point.x ?? point.X), y: Number(point.y ?? point.Y) };
    })
    .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
}

// image_transform이 없을 때만 쓰는 임시 대체 투영 (맵 이미지와는 정렬이 보장되지 않음)
function buildFallbackProjector(points: { x: number; y: number }[], size: number) {
  console.warn('[RobotMap] image_transform이 없어 graph_nodes/waypoints를 자체 bounding box로 임시 정렬합니다. 맵 이미지와 좌표가 어긋날 수 있습니다.');
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;
  const padding = 30;

  return (x: number, y: number) => ({
    cx: ((x - xMin) / xRange) * (size - padding * 2) + padding,
    cy: size - (((y - yMin) / yRange) * (size - padding * 2) + padding)
  });
}

const drawGraphOverlay = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, map: RobotMapItem, fit: CanvasFit | null) => {
  const nodes = toNodes(map.graph_nodes);
  const edges = toEdges(map.graph_edges);
  const waypoints = toWaypoints(map.waypoints);

  const allPoints = [...nodes, ...waypoints];
  if (allPoints.length === 0) return;

  const transform = map.image_transform;
  const toCanvasPoint = transform && fit
    ? (x: number, y: number) => worldToCanvas(x, y, transform, fit)
    : buildFallbackProjector(allPoints, canvas.width);

  if (waypoints.length > 1) {
    ctx.beginPath();
    waypoints.forEach((p, i) => {
      const { cx, cy } = toCanvasPoint(p.x, p.y);
      if (i === 0) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    });
    ctx.strokeStyle = '#b2b8db';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  const nodeById = new Map(nodes.map((n) => [String(n.id), n]));
  ctx.strokeStyle = '#8b93c4';
  ctx.lineWidth = 1.5;
  edges.forEach((e) => {
    const from = nodeById.get(String(e.from));
    const to = nodeById.get(String(e.to));
    if (!from || !to) return;
    const a = toCanvasPoint(from.x, from.y);
    const b = toCanvasPoint(to.x, to.y);
    ctx.beginPath();
    ctx.moveTo(a.cx, a.cy);
    ctx.lineTo(b.cx, b.cy);
    ctx.stroke();
  });

  nodes.forEach((n) => {
    const { cx, cy } = toCanvasPoint(n.x, n.y);
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#4250ab';
    ctx.fill();
  });
};

const renderMap = () => {
  const canvas = mapCanvasRef.value;
  const ctx = canvas?.getContext('2d');
  if (!canvas || !ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const map = mapStore.currentMap;
  if (!map) return;

  // image_transform 기준으로 이미지와 그래프 오버레이를 같은 스케일/오프셋으로 배치
  const fit = map.image_transform ? computeCanvasFit(map.image_transform, canvas.width) : null;

  const imageData = map.image_data;
  if (!imageData) {
    drawGraphOverlay(ctx, canvas, map, fit);
    return;
  }

  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const activeFit = fit ?? {
      scale: Math.min(canvas.width / img.width, canvas.height / img.height),
      offsetX: 0,
      offsetY: 0
    };
    if (!fit) {
      activeFit.offsetX = (canvas.width - img.width * activeFit.scale) / 2;
      activeFit.offsetY = (canvas.height - img.height * activeFit.scale) / 2;
    }
    ctx.drawImage(img, activeFit.offsetX, activeFit.offsetY, img.width * activeFit.scale, img.height * activeFit.scale);
    drawGraphOverlay(ctx, canvas, map, fit);
  };
  img.src = imageData;
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