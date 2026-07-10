// src/utils/mapCanvasRenderer.ts
// 맵 이미지 + graph_nodes/graph_edges/waypoints를 canvas에 그리는 순수 렌더링 로직.
// RobotMap.vue(대시보드, read-only)와 RobotPatrolSetting.vue(설정, 편집 가능)가
// 동일한 베이스 렌더링을 공유하기 위해 Vue 의존성 없이 분리했다.

import { computeCanvasFit, worldToCanvas, type CanvasFit } from './mapTransform';
import type { RobotMapItem } from '../stores/robotMapStore';

export interface GraphNode { id: string | number; x: number; y: number; }
export interface GraphEdge { from: string | number; to: string | number; }
export interface WaypointPoint { x: number; y: number; }

// 백엔드가 배열([{...}]) 또는 스펙 문서의 객체 맵({Node1:{...}}) 형태 중 무엇을 보내도 처리하도록 정규화
export function toNodes(raw: unknown): GraphNode[] {
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

export function toEdges(raw: unknown): GraphEdge[] {
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

export function toWaypoints(raw: unknown): WaypointPoint[] {
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
export function buildFallbackProjector(points: { x: number; y: number }[], size: number) {
  console.warn('[mapCanvasRenderer] image_transform이 없어 graph_nodes/waypoints를 자체 bounding box로 임시 정렬합니다. 맵 이미지와 좌표가 어긋날 수 있습니다.');
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

export function drawGraphOverlay(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement, map: RobotMapItem, fit: CanvasFit | null) {
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
    ctx.strokeStyle = '#808dd8';
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
}

// 맵 이미지 + graph 오버레이를 canvas에 그린다. 이미지가 비동기로 로드되므로,
// 베이스 렌더링이 끝난 시점(이미지 없음/로드 완료 둘 다)에 onBaseRendered(fit)이 호출된다.
// 편집 화면(RobotPatrolSetting)은 이 콜백에서 draft 오버레이를 이어서 그리면 된다.
export function renderMapToCanvas(
  canvas: HTMLCanvasElement,
  map: RobotMapItem | null,
  onBaseRendered?: (fit: CanvasFit | null) => void
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!map) {
    onBaseRendered?.(null);
    return;
  }

  const fit = map.image_transform ? computeCanvasFit(map.image_transform, canvas.width) : null;

  const imageData = map.image_data;
  if (!imageData) {
    drawGraphOverlay(ctx, canvas, map, fit);
    onBaseRendered?.(fit);
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
    onBaseRendered?.(fit ?? activeFit);
  };
  img.src = imageData;
}
