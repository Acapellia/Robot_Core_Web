// src/stores/robotMapStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

// render_topview_image가 world(x,y) -> 이미지 픽셀로 변환할 때 쓴 기준값.
// 그래프/로봇 위치/사용자 입력 좌표를 이미지와 동일한 좌표계로 그리려면 이 값을 그대로 재사용해야 한다.
export interface ImageTransform {
    x_min: number;
    x_max: number;
    y_min: number;
    y_max: number;
    pixel_size: number;
    padding: number;
    img_w: number;
    img_h: number;
}

// 백엔드 ALLMAPDATA 파이프라인(_parse_all_map_data)이 내려주는 맵 1개 항목 구조
export interface RobotMapItem {
    filename: string;
    frame_id?: string;
    encoding?: string;
    datasize?: number;
    pcd_data: string;
    image_path: string | null;
    image_data: string | null; // base64 PNG data URL (data:image/png;base64,...)
    image_transform: ImageTransform | null;
    graph_nodes: unknown[];
    graph_edges: unknown[];
    waypoints: unknown[];
}

export const useRobotMapStore = defineStore('robotMap', () => {
    const maps = ref<RobotMapItem[]>([]);
    const currentIndex = ref<number>(0);

    let socket: WebSocket | null = null;

    const currentMap = computed<RobotMapItem | null>(() => maps.value[currentIndex.value] ?? null);

    /**
     * 🔌 /ws/robots/maps 전용 채널로부터 ALL_MAP_DATA_UPDATE 패킷을 실시간으로 전달받는 코어 액션
     */
    const connectWebSocket = () => {
        if (socket) return; // 중복 연결 방지

        socket = new WebSocket('ws://localhost:8000/ws/robots/maps');

        socket.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                const payload = response.payload;

                if (!payload) return;

                if (payload.type === 'ALL_MAP_DATA_UPDATE') {
                    updateMaps(payload.maps ?? []);
                }
            } catch (error) {
                console.error('맵 스토어 실시간 소켓 바인딩 실패:', error);
            }
        };

        socket.onclose = () => {
            console.warn('맵 웹소켓 연결이 끊겼습니다. 3초 후 재연결을 시도합니다.');
            socket = null;
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
            console.error('맵 웹소켓 에러 발생:', err);
        };
    };

    /**
     * 🚚 수신한 맵 전체 목록으로 스토어를 통째로 동기화하는 액션
     */
    const updateMaps = (incomingMaps: RobotMapItem[]) => {
        maps.value = incomingMaps;
        if (currentIndex.value >= incomingMaps.length) {
            currentIndex.value = 0;
        }
    };

    const nextMap = () => {
        if (maps.value.length === 0) return;
        currentIndex.value = (currentIndex.value + 1) % maps.value.length;
    };

    const prevMap = () => {
        if (maps.value.length === 0) return;
        currentIndex.value = (currentIndex.value - 1 + maps.value.length) % maps.value.length;
    };

    function stopMonitoring() {
        if (socket) {
            socket.close();
            socket = null;
        }
    }

    return {
        maps,
        currentIndex,
        currentMap,
        connectWebSocket,
        updateMaps,
        nextMap,
        prevMap,
        stopMonitoring
    };
});
