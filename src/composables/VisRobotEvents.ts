// src/composables/VisRobotEvents.ts
import { storeToRefs } from 'pinia';
import { useEventStore } from '../stores/eventStore';

export function useRobotEvents() {
  const store = useEventStore();
  const { events, isLoading, error } = storeToRefs(store);

  return {
    events,
    isLoading,
    error,
    fetchEvents: store.fetchEvents,
    downloadLogCsv: store.downloadLogCsv,
    addEvent: store.addEvent,
    startMonitoring: store.startMonitoring,
    stopMonitoring: store.stopMonitoring
  };
}