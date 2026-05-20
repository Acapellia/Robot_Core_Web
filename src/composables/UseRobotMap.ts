// src/composables/UseRobotMap.ts
import { ref, onMounted, onUnmounted } from 'vue';

// 1. 백엔드에서 받아올 데이터 구조 정의
export interface Position {
  x: number;
  y: number;
}

export interface MapTelemetry {
  mapName: string;
  robotName: string;
  robotStatus: 'Patrolling' | 'Idle' | 'Offline';
  robotPosition: Position;     // 로봇의 현재 실시간 좌표
  patrolPath: Position[];      // 로봇이 따라가야 할 점선 경로 좌표 리스트
}

export function useRobotMap() {
  const mapInfo = ref<MapTelemetry | null>(null);
  const isLoading = ref<boolean>(false);
  
  // 💡 확대/축소 배율 상태 관리
  const zoomLevel = ref<number>(100);
  const maxZoom = 200;
  const minZoom = 50;

  // 2. 백엔드 API로부터 실시간 맵 및 로봇 좌표 수신 (시뮬레이션)
  const fetchMapTelemetry = async () => {
    try {
      // 실제 환경: const response = await axios.get('/api/map/telemetry');
      const mockData: MapTelemetry = {
        mapName: 'Robot Patrol Map',
        robotName: 'NEO-01 (Main)',
        robotStatus: 'Patrolling',
        // 이미지 속 중앙 마커의 위치를 상대 좌표(%)로 매핑
        robotPosition: { x: 50, y: 52 }, 
        // 이미지에 그려진 기역(ㄱ)자 및 니은(ㄴ)자 점선 이동 경로 좌표셋
        patrolPath: [
          { x: 25, y: 20 },
          { x: 50, y: 20 },
          { x: 50, y: 52 },
          { x: 50, y: 76 },
          { x: 75, y: 76 }
        ]
      };

      mapInfo.value = mockData;
    } catch (err) {
      console.error('맵 실시간 데이터를 가져오는 중 오류 발생:', err);
    }
  };

  // 3. 💡 나중에 세부 인터랙션을 붙일 수 있도록 명시적으로 분리한 맵 제어 함수들
  const zoomIn = () => {
    if (zoomLevel.value < maxZoom) {
      zoomLevel.value += 10;
      console.log(`[Map Engine] Zoomed In: ${zoomLevel.value}%`);
    }
  };

  const zoomOut = () => {
    if (zoomLevel.value > minZoom) {
      zoomLevel.value -= 10;
      console.log(`[Map Engine] Zoomed Out: ${zoomLevel.value}%`);
    }
  };

  let pollingInterval: ReturnType<typeof setInterval> | null = null;

  onMounted(() => {
    isLoading.value = true;
    fetchMapTelemetry();
    isLoading.value = false;

    // 로봇의 실시간 이동을 추적하기 위해 1초 간격으로 폴링 동기화
    pollingInterval = setInterval(fetchMapTelemetry, 1000);
  });

  onUnmounted(() => {
    if (pollingInterval) clearInterval(pollingInterval);
  });

  return {
    mapInfo,
    isLoading,
    zoomLevel,
    zoomIn,
    zoomOut
  };
}