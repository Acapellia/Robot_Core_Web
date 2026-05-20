// src/composables/UseRobotList.ts
import { ref, onMounted, onUnmounted } from 'vue';

export type RobotStatus = 'Patrolling' | 'Idle' | 'Offline';

export interface RobotItem {
  id: string;
  name: string;
  isMain: boolean;
  status: RobotStatus;
  imageUrl: string; // 💡 백엔드 API에서 받아올 로봇 이미지 URL 필드 추가
}

export function useRobotList() {
  const robots = ref<RobotItem[]>([]);
  const selectedRobotId = ref<string | null>(null);
  const isLoading = ref<boolean>(false);
  let pollingTimer: ReturnType<typeof setInterval> | null = null;

  const fetchrobotData = async () => {
    try {
      // 백엔드 API 연동 시뮬레이션 (실제 서빙 시 로봇별 이미지 경로가 포함됩니다)
      const mockData: RobotItem[] = [
        { id: 'neo-01', name: 'NEO-01', isMain: true, status: 'Patrolling', imageUrl: '' },
        { id: 'neo-02', name: 'NEO-02', isMain: false, status: 'Idle', imageUrl: '' },
        { id: 'neo-03', name: 'NEO-03', isMain: false, status: 'Offline', imageUrl: '' }
      ];

      robots.value = mockData;

      if (!selectedRobotId.value && mockData.length > 0) {
        selectedRobotId.value = mockData[0].id;
      }
    } catch (err) {
      console.error('로봇 리스트 데이터를 가져오는 중 오류 발생:', err);
    }
  };

  const selectRobot = (id: string) => {
    selectedRobotId.value = id;
  };

  onMounted(() => {
    isLoading.value = true;
    fetchrobotData();
    isLoading.value = false;

    pollingTimer = setInterval(fetchrobotData, 5000);
  });

  onUnmounted(() => {
    if (pollingTimer) clearInterval(pollingTimer);
  });

  return {
    robots,
    selectedRobotId,
    isLoading,
    selectRobot
  };
}