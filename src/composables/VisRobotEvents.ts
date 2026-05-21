// src/composables/VisRobotEvents.ts
import { storeToRefs } from 'pinia';
import { useEventStore } from '../stores/eventStore';

export function useRobotEvents() {
  const store = useEventStore();
  const { events, isLoading, error } = storeToRefs ? storeToRefs(store) : store;

  // Expose store actions directly
  return {
    events,
    isLoading,
    error,
    fetchEvents: store.fetchEvents,
    downloadLogCsv: store.downloadLogCsv
  };
}