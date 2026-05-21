// src/composables/UseRobotInfo.ts
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRobotStore, RobotTelemetry } from '../stores/robotStore';

export function useRobotInfo() {
  const robotInfo = ref<RobotTelemetry | null>(null);
  const isLoading = ref<boolean>(false);
  let metricsTimer: ReturnType<typeof setInterval> | null = null;
  const robotStore = useRobotStore();
  const { robots } = storeToRefs(robotStore);

  const fetchRobotInfo = async () => {
    try {
      // 기본(로컬) 상세값
      const mockDetail: RobotTelemetry = {
        name: 'NEO-01',
        version: 'v2.4.0',
        ipAddress: '192.168.1.104',
        status: 'PATROLLING',
        battery: 84,
        currentMap: 'Floor_L2_North',
        uptime: '12h 45m'
      };

      const main = robots.value.find(r => r.isMain === true);
      if (main && main.telemetry) {
        mockDetail.name = main.telemetry.name ?? mockDetail.name;
        mockDetail.ipAddress = main.telemetry.ipAddress ?? mockDetail.ipAddress;
        mockDetail.status = main.telemetry.status ?? mockDetail.status;
        mockDetail.battery = main.telemetry.battery ?? mockDetail.battery;
        mockDetail.currentMap = main.telemetry.currentMap ?? mockDetail.currentMap;
        mockDetail.uptime = main.telemetry.uptime ?? mockDetail.uptime;
      }

      robotInfo.value = mockDetail;

    } catch (err) {
      console.error('로봇 상세 정보를 가져오는 중 오류 발생:', err);
    }
  };

  onMounted(() => {
    isLoading.value = true;
    fetchRobotInfo();
    isLoading.value = false;
    metricsTimer = setInterval(fetchRobotInfo, 3000);
    // react to robot list changes to update displayed name/ip immediately
    watch(robots, () => {
      fetchRobotInfo();
    });
  });

  onUnmounted(() => {
    if (metricsTimer) clearInterval(metricsTimer);
  });

  return {
    robotInfo,
    isLoading
  };
}