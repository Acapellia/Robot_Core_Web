// src/composables/UseRobotInfo.ts
import { ref, onMounted, onUnmounted } from 'vue';

export interface RobotTelemetry {
  name: string;
  version: string;
  ipAddress: string;
  status: 'PATROLLING' | 'IDLE' | 'OFFLINE';
  battery: number;
  currentMap: string;
  uptime: string;
}

export function useRobotInfo() {
  const robotInfo = ref<RobotTelemetry | null>(null);
  const isLoading = ref<boolean>(false);
  let metricsTimer: ReturnType<typeof setInterval> | null = null;

  const fetchRobotInfo = async () => {
    try {
      // 이미지 스펙 데이터 기반 Mocking
      const mockDetail: RobotTelemetry = {
        name: 'NEO-01',
        version: 'v2.4.0',
        ipAddress: '192.168.1.104',
        status: 'PATROLLING',
        battery: 84,
        currentMap: 'Floor_L2_North',
        uptime: '12h 45m'
      };
      robotInfo.value = mockDetail;
    } catch (err) {
      console.error('로봇 상세 정보를 가져오는 중 오류 발생:', err);
    }
  };

  onMounted(() => {
    isLoading.value = true;
    fetchRobotInfo();
    isLoading.value = false;
    metricsTimer = setInterval(fetchRobotInfo, 3000);
  });

  onUnmounted(() => {
    if (metricsTimer) clearInterval(metricsTimer);
  });

  return {
    robotInfo,
    isLoading
  };
}