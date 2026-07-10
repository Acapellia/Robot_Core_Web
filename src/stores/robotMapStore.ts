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
    // ALL_MAP_DATA_UPDATE는 허브(로봇)마다 독립적으로 도착하므로, 허브 연결 식별자(예: hub_{ip}_{port})별로
    // 맵 목록을 분리 보관한다. 이렇게 하지 않으면 여러 로봇의 맵이 하나의 배열에 뒤섞여 마지막으로 수신한
    // 허브의 맵만 항상 표시되는 문제가 생긴다.
    const mapsBySource = ref<Record<string, RobotMapItem[]>>({});
    const currentIndexBySource = ref<Record<string, number>>({});
    // 화면에 표시할 대상 허브의 소스 키. 사용하는 컴포넌트가 선택된 로봇/허브에 맞춰 설정한다.
    const activeSource = ref<string | null>(null);

    let socket: WebSocket | null = null;

    const maps = computed<RobotMapItem[]>(() =>
        activeSource.value ? mapsBySource.value[activeSource.value] ?? [] : []
    );

    const currentIndex = computed<number>(() =>
        activeSource.value ? currentIndexBySource.value[activeSource.value] ?? 0 : 0
    );

    const currentMap = computed<RobotMapItem | null>(() => maps.value[currentIndex.value] ?? null);

    const setActiveSource = (source: string | null) => {
        activeSource.value = source;
    };

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
                // 이 맵 목록을 보낸 허브 연결 식별자 (예: hub_{ip}_{port})
                const source: string | undefined = response.source;

                if (!payload || !source) return;

                if (payload.type === 'ALL_MAP_DATA_UPDATE') {
                    updateMaps(source, payload.maps ?? []);
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
     * 🚚 특정 허브로부터 수신한 맵 전체 목록으로 해당 허브분만 동기화하는 액션
     */
    const updateMaps = (source: string, incomingMaps: RobotMapItem[]) => {
        mapsBySource.value = { ...mapsBySource.value, [source]: incomingMaps };
        const idx = currentIndexBySource.value[source] ?? 0;
        if (idx >= incomingMaps.length) {
            currentIndexBySource.value = { ...currentIndexBySource.value, [source]: 0 };
        }
    };

    const nextMap = () => {
        const source = activeSource.value;
        if (!source) return;
        const list = mapsBySource.value[source] ?? [];
        if (list.length === 0) return;
        const idx = currentIndexBySource.value[source] ?? 0;
        currentIndexBySource.value = { ...currentIndexBySource.value, [source]: (idx + 1) % list.length };
    };

    const prevMap = () => {
        const source = activeSource.value;
        if (!source) return;
        const list = mapsBySource.value[source] ?? [];
        if (list.length === 0) return;
        const idx = currentIndexBySource.value[source] ?? 0;
        currentIndexBySource.value = { ...currentIndexBySource.value, [source]: (idx - 1 + list.length) % list.length };
    };

    /**
     * ✍️ 순찰 웨이포인트 저장 성공 직후, 허브 ack를 기다리지 않고 현재 맵에 낙관적으로 반영하는 액션.
     * Dashboard의 RobotMap.vue도 동일 스토어를 구독하므로, 같은 허브가 선택되어 있다면 즉시 함께 갱신된다.
     */
    const setWaypointsForCurrentMap = (waypoints: { x: number; y: number }[]) => {
        const source = activeSource.value;
        const map = currentMap.value;
        if (!source || !map) return;
        mapsBySource.value = {
            ...mapsBySource.value,
            [source]: (mapsBySource.value[source] ?? []).map((m) => (m === map ? { ...m, waypoints } : m))
        };
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
        activeSource,
        setActiveSource,
        connectWebSocket,
        updateMaps,
        nextMap,
        prevMap,
        setWaypointsForCurrentMap,
        stopMonitoring
    };
});
