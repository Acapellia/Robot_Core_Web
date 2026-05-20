// src/composables/VisRobotEvents.ts
import { ref, onMounted, onUnmounted } from 'vue';

// 1. 타입 정의 (인터페이스 배포)
export interface RobotEvent {
  id: number; // 가급적 고유 ID를 백엔드에서 받아오는 것이 안전합니다.
  type: 'INFO' | 'ALERT' | 'SYSTEM' | 'WARNING';
  time: string;
  message: string;
}

export function useRobotEvents() {
  const events = ref<RobotEvent[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);
  
  // 가상의 타이머 ID (실시간 데이터 폴링용)
  let pollingTimer: ReturnType<typeof setInterval> | null = null;

  // 2. 백엔드 API 호출 함수 (추후 axios 등으로 대체)
  const fetchEvents = async () => {
    isLoading.value = true;
    error.value = null;
    try {
      // API 호출 시뮬레이션 (네트워크 지연 500ms)
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      // 실제 환경에서는: const response = await axios.get('/api/robot/events');
      const mockData: RobotEvent[] = [
        { id: 1, type: 'INFO', time: '14:32:01', message: 'System check completed. All subsystems nominal.' },
        { id: 2, type: 'ALERT', time: '14:31:48', message: 'Path L2-4 blocked by static obstacle.' },
        { id: 3, type: 'SYSTEM', time: '14:30:12', message: 'Robot position synchronized with local map.' },
        { id: 4, type: 'WARNING', time: '14:28:55', message: 'Unusual temperature spike in Section C (28°C).' },
        { id: 5, type: 'INFO', time: '14:25:00', message: 'Routine patrol mission "Full Scan" started.' },
        { id: 6, type: 'SYSTEM', time: '14:10:22', message: 'Docking successful. Charging initiated.' },
        { id: 7, type: 'SYSTEM', time: '14:20:22', message: 'Flame Event is detected.' },
        { id: 8, type: 'INFO', time: '14:32:01', message: 'System check completed. All subsystems nominal.' },
        { id: 9, type: 'ALERT', time: '14:31:48', message: 'Path L2-4 blocked by static obstacle.' },
        { id: 10, type: 'SYSTEM', time: '14:30:12', message: 'Robot position synchronized with local map.' },
        { id: 11, type: 'WARNING', time: '14:28:55', message: 'Unusual temperature spike in Section C (28°C).' },
        { id: 12, type: 'INFO', time: '14:25:00', message: 'Routine patrol mission "Full Scan" started.' },
        { id: 13, type: 'SYSTEM', time: '14:10:22', message: 'Docking successful. Charging initiated.' },
        { id: 14, type: 'SYSTEM', time: '14:20:22', message: 'Flame Event is detected.' },
        { id: 15, type: 'INFO', time: '14:32:01', message: 'System check completed. All subsystems nominal.' },
        { id: 16, type: 'ALERT', time: '14:31:48', message: 'Path L2-4 blocked by static obstacle.' },
        { id: 17, type: 'SYSTEM', time: '14:30:12', message: 'Robot position synchronized with local map.' },
        { id: 18, type: 'WARNING', time: '14:28:55', message: 'Unusual temperature spike in Section C (28°C).' },
        { id: 19, type: 'INFO', time: '14:25:00', message: 'Routine patrol mission "Full Scan" started.' },
        { id: 20, type: 'SYSTEM', time: '14:10:22', message: 'Docking successful. Charging initiated.' },
        { id: 21, type: 'SYSTEM', time: '14:20:22', message: 'Flame Event is detected.' }
      ];
      
      events.value = mockData;
    } catch (err) {
      error.value = '이벤트 로그를 불러오는 중 오류가 발생했습니다.';
      console.error(err);
    } finally {
      isLoading.value = false;
    }
  };

  // 3. CSV 다운로드 기능 비즈니스 로직
  const downloadLogCsv = () => {
    if (events.value.length === 0) return alert('다운로드할 로그가 없습니다.');
    
    const csvContent = "data:text/csv;charset=utf-8," 
      + ["Type,Time,Message", ...events.value.map(e => `"${e.type}","${e.time}","${e.message}"`)].join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `robot_event_log_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 4. 생명주기 관리 (컴포넌트 장착 시 자동 조회 및 주기적 갱신 설정)
  onMounted(() => {
    fetchEvents();
    // 관제 시스템 특성상 10초마다 새로운 로그를 받아오도록 폴링 스케줄러 등록 가능
    pollingTimer = setInterval(fetchEvents, 10000);
  });

  onUnmounted(() => {
    // 컴포넌트 파괴 시 메모리 누수 방지를 위해 타이머 해제
    if (pollingTimer) clearInterval(pollingTimer);
  });

  return {
    events,
    isLoading,
    error,
    fetchEvents,
    downloadLogCsv
  };
}