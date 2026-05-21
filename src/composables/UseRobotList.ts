// src/composables/UseRobotList.ts
import { storeToRefs } from 'pinia';
import { useRobotStore } from '../stores/robotStore';

/**
 * 로봇 목록 대시보드 제어를 담당하는 컴포저블 함수
 */
export function useRobotList() {
  // 1. 전역 Pinia 창고를 불러옵니다.
  const store = useRobotStore();
  
  // 2. Pinia 창고 안의 상태(Ref)를 안전하게 꺼내옵니다. (반응형 유지를 위해 storeToRefs 사용)
  const { robots, selectedRobotId } = storeToRefs(store);
  
  // 3. Pinia 창고 안의 기능(액션)을 꺼내옵니다.
  const { selectRobot } = store;

  /**
   * 💡 [현재 단계]: 백엔드가 없으므로 순수하게 Pinia 창고 데이터만 화면에 토스합니다.
   * 
   * 🛠️ [나중 단계]: FastAPI 웹소켓이 완성되면 여기에 아래 주석 친 코드를 합치면 끝납니다.
   * 
   * import { onMounted, onUnmounted } from 'vue';
   * let socket: WebSocket | null = null;
   * 
   * onMounted(() => {
   *   socket = new WebSocket('ws://localhost:8000/ws/robots');
   *   socket.onmessage = (event) => {
   *     const data = JSON.parse(event.data);
   *     store.updateRobot(data); // 🚚 실시간 수신 데이터를 Pinia 창고로 배달!
   *   };
   * });
   * 
   * onUnmounted(() => {
   *   if (socket) socket.close();
   * });
   */

  // 4. 화면(RobotSelect.vue)에서 바인딩해서 쓸 알맹이들만 반환합니다.
  return {
    robots,
    selectedRobotId,
    selectRobot
  };
}