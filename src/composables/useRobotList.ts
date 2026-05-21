// src/composables/UseRobotList.ts
import { storeToRefs } from 'pinia';
import { useRobotStore } from '../stores/robotStore';
import { onMounted, onUnmounted } from 'vue';

// 로봇 목록 대시보드 제어를 담당하는 컴포저블 함수
 
export function useRobotList() {
  // 1. 전역 Pinia 창고를 불러옵니다.
  const store = useRobotStore();
  
  // 2. Pinia 창고 안의 상태(Ref)를 안전하게 꺼내옵니다. (반응형 유지를 위해 storeToRefs 사용)
  const { robots, selectedRobotId } = storeToRefs(store);
  
  // 3. Pinia 창고 안의 기능(액션)을 꺼내옵니다.
  const { selectRobot } = store;

  return {
    robots,
    selectedRobotId,
    selectRobot
  };
}