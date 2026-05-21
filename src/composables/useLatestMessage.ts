import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useEventStore, EventType } from '../stores/eventStore';

export interface LatestAlert {
  message: string;
  time: string;
  type: EventType;
}

export function useLatestAlert() {
  const store = useEventStore();
  const { events } = storeToRefs(store);

  const latestAlert = computed<LatestAlert | null>(() => {
    const list = events.value;
    if (!list || list.length === 0) return null;
    const last = list[0];
    return { message: last.message, time: last.time, type: last.type } as LatestAlert;
  });

  return { latestAlert };
}