// src/composables/UseHeader.ts
import { ref, onMounted, onUnmounted } from 'vue';

export function useHeader() {
  const currentTime = ref<string>('');
  let timer: ReturnType<typeof setInterval> | null = null;

  // 년.월.일 시:분 포맷팅 함수
  const updateTime = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const date = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    currentTime.value = `${year}.${month}.${date} ${hours}:${minutes}`;
  };

  onMounted(() => {
    updateTime();
    // 매 초마다 체크하여 분이 바뀔 때 매끄럽게 동기화
    timer = setInterval(updateTime, 1000);
  });

  onUnmounted(() => {
    if (timer) clearInterval(timer);
  });

  return {
    currentTime
  };
}