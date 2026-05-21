// src/strores/robotStore.ts

import { defineStore } from 'pinia';
import { ref } from 'vue';

export type RobotStatus = 'Patrolling' | 'Idle' | 'Offline';

export interface RobotItem {
  id: string;
  name: string;
  ip: string;
  isMain: boolean;
  status: RobotStatus;
  imageUrl: string; // 💡 백엔드 API에서 받아올 로봇 이미지 URL 필드 추가
}

// 💡 1. 가짜 데이터(Mock)는 함수 외부로 분리합니다. 
// 나중에 서버 연동이 완료되면 이 배열을 빈 배열([])로 바꾸기만 하면 됩니다.
const INITIAL_MOCK_DATA: RobotItem[] = [
  { id: 'neo-01', name: 'NEO-01', ip: '172.16.15.27', isMain: true, status: 'Patrolling', imageUrl: '' },
  { id: 'neo-02', name: 'NEO-02', ip: '192.168.1.104', isMain: false, status: 'Idle', imageUrl: '' },
  { id: 'neo-03', name: 'NEO-03', ip: '195.6.14.1', isMain: false, status: 'Offline', imageUrl: '' }
];

export const useRobotStore = defineStore('robot', () => {
    const robots = ref<RobotItem[]>(INITIAL_MOCK_DATA);
    const selectedRobotId = ref<string | null>(robots.value[0]?.id || null);

    /**
     * 🔌 추후 FastAPI 웹소켓으로부터 데이터를 실시간으로 전달받아 처리하는 액션(함수)
     * - 웹소켓 컴포저블이 이 함수를 호출하여 데이터를 주입합니다.
     * - 이 함수는 MOCK_ROBOTS 상수가 아니라 위의 'robots.value' 창고 데이터만 제어합니다.
     */
   const updateRobot = (serverData: RobotItem) => {
        // 1. 현재 창고(robots.value)에 이미 존재하는 로봇 번호인지 확인
        const existingRobot = robots.value.find(r => r.id === serverData.id);

        if (existingRobot) {
            // 2. 이미 존재하는 로봇이면 상태와 이미지 URL을 업데이트
            existingRobot.status = serverData.status;
            existingRobot.imageUrl = serverData.imageUrl;
            existingRobot.isMain = serverData.isMain;
        } else {
            // 3. 존재하지 않는 로봇이면 새로 추가 (예: 새로운 로봇이 연결된 경우)
            robots.value.push(serverData);
        }
    };

    /**
     * 화면에서 로봇 아이템을 마우스로 클릭했을 때 호출 액션
     */
    const selectRobot = (id: string) => {
        selectedRobotId.value = id;
    };

    return {
        robots,
        selectedRobotId,
        updateRobot,
        selectRobot
    };

});