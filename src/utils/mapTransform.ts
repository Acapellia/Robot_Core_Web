// src/utils/mapTransform.ts
// 백엔드의 render_topview_image가 world(x,y) -> 이미지 픽셀로 투영할 때 쓰는 공식과 동일한 변환을 재현한다.
// 맵 이미지, graph_nodes/edges/waypoints, 로봇 실시간 위치, 사용자가 캔버스에 입력하는 순찰 경로까지
// 전부 이 유틸 하나를 거쳐야 서로 같은 좌표계로 정렬된다.

import type { ImageTransform } from '../stores/robotMapStore';

export interface CanvasFit {
    scale: number;
    offsetX: number;
    offsetY: number;
}

// 이미지(img_w x img_h)를 정사각형 canvas(canvasSize) 안에 contain-fit으로 중앙 배치했을 때의 스케일/오프셋
export function computeCanvasFit(transform: ImageTransform, canvasSize: number): CanvasFit {
    const scale = Math.min(canvasSize / transform.img_w, canvasSize / transform.img_h);
    return {
        scale,
        offsetX: (canvasSize - transform.img_w * scale) / 2,
        offsetY: (canvasSize - transform.img_h * scale) / 2
    };
}

// world(x, y) -> canvas 픽셀 좌표. pcd_map_parser.py의 render_topview_image 공식과 1:1 대응.
export function worldToCanvas(x: number, y: number, transform: ImageTransform, fit: CanvasFit): { cx: number; cy: number } {
    const xRange = transform.x_max - transform.x_min || 1;
    const yRange = transform.y_max - transform.y_min || 1;

    const imgX = ((x - transform.x_min) / xRange) * (transform.img_w - transform.padding * 2) + transform.padding;
    const imgY = ((transform.y_max - y) / yRange) * (transform.img_h - transform.padding * 2) + transform.padding;

    return {
        cx: imgX * fit.scale + fit.offsetX,
        cy: imgY * fit.scale + fit.offsetY
    };
}

// canvas 픽셀 좌표 -> world(x, y). 사용자가 캔버스에서 클릭/드로잉한 지점을 로봇이 이해하는 좌표로 보낼 때 사용.
export function canvasToWorld(cx: number, cy: number, transform: ImageTransform, fit: CanvasFit): { x: number; y: number } {
    const imgX = (cx - fit.offsetX) / fit.scale;
    const imgY = (cy - fit.offsetY) / fit.scale;

    const xRange = transform.x_max - transform.x_min || 1;
    const yRange = transform.y_max - transform.y_min || 1;

    const x = ((imgX - transform.padding) / (transform.img_w - transform.padding * 2)) * xRange + transform.x_min;
    const y = transform.y_max - ((imgY - transform.padding) / (transform.img_h - transform.padding * 2)) * yRange;

    return { x, y };
}
