// src/composables/useLatestAlert.ts
import { ref, onMounted, onUnmounted } from 'vue';

export interface LatestAlert {
  message: string;
  time: string;
}

export function useLatestAlert() {
  const latestAlert = ref<LatestAlert | null>(null);
  const isLoading = ref<boolean>(false);
  let pollingTimer: ReturnType<typeof setInterval> | null = null;

  const fetchLatestAlert = async () => {
    try {
      // 실제 환경: const response = await axios.get('/api/robot/latest-alert');
      // 백엔드 API 호출을 시뮬레이션합니다.
      const mockData: LatestAlert = {
        message: 'LATEST ALERT: Minor obstruction detected on path L2-4. Robot rerouting...',
        time: '14:31:48'
      };
      
      latestAlert.value = mockData;
    } catch (err) {
      console.error('최신 알림을 가져오는 중 오류 발생:', err);
    }
  };

  onMounted(() => {
    fetchLatestAlert();
    // 관제 특성상 5초마다 최신 알림 스캔 (혹은 WebSocket 이벤트 바인딩으로 대체 가능)
    pollingTimer = setInterval(fetchLatestAlert, 5000);
  });

  onUnmounted(() => {
    if (pollingTimer) clearInterval(pollingTimer);
  });

  return {
    latestAlert,
    isLoading,
    fetchLatestAlert
  };
}