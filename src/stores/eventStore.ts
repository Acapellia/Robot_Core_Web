import { defineStore } from 'pinia';
import { ref } from 'vue';

export type EventType = 'INFO' | 'ALERT' | 'SYSTEM' | 'WARNING';

export interface RobotEvent {
  event_id: number;
  robot_Id: string;
  type: EventType;
  time: string;
  message: string;
}

const INITIAL_EVENTS: RobotEvent[] = [
];

export const useEventStore = defineStore('event', () => {
  const events = ref<RobotEvent[]>(INITIAL_EVENTS);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  let socket: WebSocket | null = null;

  function connectWebSocket() {
    if (socket) return;

    isLoading.value = true;
    socket = new WebSocket('ws://localhost:8000/ws/robots/events');

    socket.onmessage = (ev) => {
      try {
        const response = JSON.parse(ev.data);
        const payload = response.payload;

        if (!payload) return;

        if (payload.type === 'ROBOT_EVENT_UPDATE') {
          updateEventList(payload.robot_events);
        }
      } catch (err) {
        console.error('eventStore websocket message parse failed:', err);
      } finally {
        isLoading.value = false;
      }
    };

    socket.onclose = () => {
      console.warn('Event websocket closed, retrying in 3s');
      socket = null;
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (err) => {
      console.error('Event websocket error:', err);
      error.value = '웹소켓 에러';
    };
  }

  const updateEventList = (robotEvents: RobotEvent[]) => {
    // 대입 말고 추가가 되어야 함
    // events.value = robotEvents;
    events.value = [...events.value, ...robotEvents].slice(0, 100);
  };

  function startMonitoring() {
    connectWebSocket();
  }

  function stopMonitoring() {
    if (socket) {
      socket.close();
      socket = null;
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

  return { events, isLoading, error, startMonitoring, stopMonitoring, downloadLogCsv };
});
