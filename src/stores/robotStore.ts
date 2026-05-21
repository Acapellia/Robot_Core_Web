// src/strores/robotStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';

export type RobotStatus = 'PATROLLING' | 'IDLE' | 'OFFLINE';

export interface RobotTelemetry {
    name: string;
    version?: string;
    ipAddress?: string;
    status: RobotStatus;
    battery?: number;
    currentMap?: string;
    uptime?: string;
}

export interface RobotItem {
    id: string;
    telemetry: RobotTelemetry;
    isMain: boolean;
    imageUrl: string; // 백엔드 API에서 받아올 로봇 이미지 URL 필드
}

// Mock data
const INITIAL_MOCK_DATA: RobotItem[] = [
    { id: 'neo-01', telemetry: { name: 'NEO-01', ipAddress: '172.16.15.27', status: 'PATROLLING', battery: 84, currentMap: 'Floor_L2_North', uptime: '12h 45m' }, isMain: true, imageUrl: '' },
    { id: 'neo-02', telemetry: { name: 'NEO-02', ipAddress: '192.168.1.104', status: 'IDLE', battery: 66, currentMap: 'Floor_L1_South', uptime: '2h 12m' }, isMain: false, imageUrl: '' },
    { id: 'neo-03', telemetry: { name: 'NEO-03', ipAddress: '195.6.14.1', status: 'OFFLINE', battery: 0, currentMap: '', uptime: '0h' }, isMain: false, imageUrl: '' }
];

export const useRobotStore = defineStore('robot', () => {
    const robots = ref<RobotItem[]>(INITIAL_MOCK_DATA);
    const selectedRobotId = ref<string | null>(robots.value[0]?.id || null);
    let timerId: ReturnType<typeof setInterval> | null = null;

    /**
     * 🔌 추후 FastAPI 웹소켓으로부터 데이터를 실시간으로 전달받아 처리하는 액션(함수)
     * - 웹소켓 컴포저블이 이 함수를 호출하여 데이터를 주입합니다.
     * - 이 함수는 MOCK_ROBOTS 상수가 아니라 위의 'robots.value' 창고 데이터만 제어합니다.
     */
   const updateRobot = (serverData: RobotItem) => {
        // check existing
        const existing = robots.value.find(r => r.id === serverData.id);
        if (existing) {
            existing.telemetry = { ...existing.telemetry, ...serverData.telemetry };
            existing.imageUrl = serverData.imageUrl ?? existing.imageUrl;
            existing.isMain = serverData.isMain;
        } else {
            robots.value.push(serverData);
        }
    };

    /**
     * 화면에서 로봇 아이템을 마우스로 클릭했을 때 호출 액션
     */
    const selectRobot = (id: string) => {
        selectedRobotId.value = id;
        // 선택된 로봇을 메인으로 설정하고, 다른 로봇들은 isMain=false로 한다.
        robots.value = robots.value.map(r => ({ ...r, isMain: r.id === id }));
    };

    async function fetchRobots() {
    }

    function startMonitoring(intervalMs = 5000) {
        if (timerId) return;
        fetchRobots();
        timerId = setInterval(fetchRobots, intervalMs);
    }

    function stopMonitoring() {
        if (timerId) {
            clearInterval(timerId);
            timerId = null;
        }
    }

    return {
        robots,
        selectedRobotId,
        updateRobot,
        selectRobot,
        fetchRobots,
        startMonitoring,
        stopMonitoring
    };

});