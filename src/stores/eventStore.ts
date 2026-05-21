import { defineStore } from 'pinia';
import { ref } from 'vue';

export type EventType = 'INFO' | 'ALERT' | 'SYSTEM' | 'WARNING';

export interface RobotEvent {
  id: number;
  type: EventType;
  time: string;
  message: string;
}

const INITIAL_EVENTS: RobotEvent[] = [
  { id: 1, type: 'INFO', time: '14:32:01', message: 'System check completed. All subsystems nominal.' },
  { id: 2, type: 'ALERT', time: '14:31:48', message: 'Path L2-4 blocked by static obstacle.' },
  { id: 3, type: 'SYSTEM', time: '14:30:12', message: 'Robot position synchronized with local map.' },
  { id: 4, type: 'WARNING', time: '14:28:55', message: 'Unusual temperature spike in Section C (28°C).' },
  { id: 5, type: 'INFO', time: '14:25:00', message: 'Routine patrol mission "Full Scan" started.' }
];

export const useEventStore = defineStore('event', () => {
  const events = ref<RobotEvent[]>(INITIAL_EVENTS);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  let timerId: ReturnType<typeof setInterval> | null = null;

  async function fetchEvents() {
    isLoading.value = true;
    error.value = null;
    try {
      // simulate delay
      await new Promise(r => setTimeout(r, 300));
      // in real app we'd fetch from /api/robot/events
      // keep existing initial data or replace
      // events.value = (await api.get('/api/robot/events')).data
    } catch (err) {
      error.value = '이벤트 로그를 불러오는 중 오류가 발생했습니다.';
      console.error(err);
    } finally {
      isLoading.value = false;
    }
  }

  function startMonitoring(intervalMs = 10000) {
    if (timerId) return;
    fetchEvents();
    timerId = setInterval(fetchEvents, intervalMs);
  }

  function stopMonitoring() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  function downloadLogCsv() {
    if (events.value.length === 0) return;
    const csvContent = "data:text/csv;charset=utf-8," + ["Type,Time,Message", ...events.value.map(e => `"${e.type}","${e.time}","${e.message}"`)].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `robot_event_log_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return { events, isLoading, error, fetchEvents, startMonitoring, stopMonitoring, downloadLogCsv };
});
