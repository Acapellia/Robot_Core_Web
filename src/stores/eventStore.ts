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
  { id: 1, type: 'INFO', time: '09:32:01', message: 'System check completed. All subsystems nominal.' },
  { id: 2, type: 'ALERT', time: '10:25:48', message: 'Path L2-4 blocked by static obstacle.' },
  { id: 3, type: 'SYSTEM', time: '13:17:12', message: 'Robot position synchronized with local map.' },
  { id: 4, type: 'WARNING', time: '14:28:55', message: 'Unusual temperature spike in Section C (28°C).' },
  { id: 5, type: 'INFO', time: '16:45:10', message: 'Routine patrol mission "Full Scan" started.' },
  { id: 6, type: 'ALERT', time: '18:00:00', message: 'Is time to go home!!' },
];

export const useEventStore = defineStore('event', () => {
  const events = ref<RobotEvent[]>(INITIAL_EVENTS);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  let timerId: ReturnType<typeof setInterval> | null = null;

  async function fetchEvents() {

  }

  // No dev simulation: events should come from backend or explicit actions

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
