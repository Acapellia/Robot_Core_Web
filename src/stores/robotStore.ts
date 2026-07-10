// src/stores/robotStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface RobotTelemetry {
    isOnline: boolean;
    battery?: number;
    statecode?: number;
    isManual?: boolean;
    locomotionMode?: string;
    isVoiceActive?: boolean;
    currentMap?: string;
    uptime?: string;
}

export interface RobotItem {
    id: string;
    robot_ip: string;
    robot_port: number;
    telemetry: RobotTelemetry;
    isMain: boolean;
    imageUrl: string; // 백엔드 API에서 받아올 로봇 이미지 URL 필드
}

// Mock data (실시간 소켓이 연결되므로 비워둡니다)
const INITIAL_MOCK_DATA: RobotItem[] = [];

export const useRobotStore = defineStore('robot', () => {
    const robots = ref<RobotItem[]>(INITIAL_MOCK_DATA);
    const selectedRobotId = ref<string | null>(null);
    
    // 내부 웹소켓 세션 상태 객체
    let socket: WebSocket | null = null;

    /**
     * 🔌 [전역 가동] FastAPI 웹소켓으로부터 데이터를 실시간으로 전달받는 코어 액션
     * - 시스템 진입점(App.vue 등)에서 최초 1회 실행해주면 백그라운드에서 계속 동작합니다.
     */
    const connectWebSocket = () => {
        if (socket) return; // 중복 연결 방지

        socket = new WebSocket('ws://localhost:8000/ws/robots/telemetry');

        socket.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                const payload = response.payload;

                if (!payload) return;

                // 1. 중계기 MessageParser가 가공한 전체 로봇 목록 패킷인 경우
                if (payload.type === 'ROBOT_LIST_UPDATE') {
                    updateRobotList(payload.robots);
                } 
                // 2. 개별 로봇 텔레메트리 업데이트 패킷인 경우
                else if (payload.type === 'ROBOT_STATE_UPDATE') {
                    updateRobotStates(payload.robot_states);
                }
            } catch (error) {
                console.error('스토어 실시간 소켓 바인딩 실패:', error);
            }
        };

        socket.onclose = () => {
            console.warn('텔레메트리 웹소켓 연결이 끊겼습니다. 3초 후 재연결을 시도합니다.');
            socket = null;
            setTimeout(connectWebSocket, 3000); // 좀비 재연결
        };

        socket.onerror = (err) => {
            console.error('웹소켓 에러 발생:', err);
        };
    };

    /**
     * 🚚 [목록 갱신] 중계기로부터 로봇 전체 목록 배열을 받아 창고를 통째로 동기화하는 액션
     */
    const updateRobotList = (incomingRobots: RobotItem[]) => {
        incomingRobots.forEach((newRobot) => {
            const existing = robots.value.find(r => r.id === newRobot.id);
            if (existing) {
                // 기존에 존재하면 네트워크 정보 최신화 (컨트롤 제어 목적)
                existing.robot_ip = newRobot.robot_ip;
                existing.robot_port = newRobot.robot_port;
            } else {
                // 새로운 로봇인 경우 기본 객체를 보강하여 밀어넣기 (isMain은 기본 false)
                robots.value.push({ ...newRobot, isMain: false });
            }
        });

        // 메인 로봇이 없으면(선택 없음) 리스트의 첫 번째 로봇을 메인으로 세팅
        const hasMain = robots.value.some(r => r.isMain === true);
        if (!hasMain && robots.value.length > 0) {
            selectedRobotId.value = robots.value[0].id;
            robots.value = robots.value.map((r, i) => ({ ...r, isMain: i === 0 }));
        }
    };

    const updateRobotStates = (robotStates: RobotItem[]) => {
        robotStates.forEach((updated) => {
            if (!updated.id) return;
            const existing = robots.value.find(r => r.id === updated.id);
            if (existing) {
                existing.telemetry = updated.telemetry;
            } else {
                // 로봇 목록 패킷(ROBOT_LIST_UPDATE)보다 상태 패킷이 먼저 도착한 경우를 대비해 신규 항목으로 추가
                robots.value.push({
                    id: updated.id,
                    robot_ip: '',
                    robot_port: 0,
                    telemetry: updated.telemetry,
                    isMain: false,
                    imageUrl: ''
                });
            }
        });

        // 메인 로봇이 없으면(선택 없음) 리스트의 첫 번째 로봇을 메인으로 세팅
        const hasMain = robots.value.some(r => r.isMain === true);
        if (!hasMain && robots.value.length > 0) {
            selectedRobotId.value = robots.value[0].id;
            robots.value = robots.value.map((r, i) => ({ ...r, isMain: i === 0 }));
        }
    };


    /**
     * 🖱️ 화면에서 로봇 아이템을 마우스로 클릭했을 때 호출 액션
     */
    const selectRobot = (id: string) => {
        selectedRobotId.value = id;
        robots.value = robots.value.map(r => ({ ...r, isMain: r.id === id }));
    };

    // 기존의 폴링 모니터링 방식은 이제 필요치 않으므로 인터페이스 통일을 위해 더미 전환
    function startMonitoring() {
        connectWebSocket();
    }

    function stopMonitoring() {
        if (socket) {
            socket.close();
            socket = null;
        }
    }

    return {
        robots,
        selectedRobotId,
        connectWebSocket,
        updateRobotList,
        selectRobot,
        startMonitoring, // 기존 컴포넌트 사이드 이펙트 방지용 유지
        stopMonitoring
    };
});