// src/composables/UseRobotInfo.ts
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRobotStore, RobotTelemetry } from '../stores/robotStore';

// robotstatus.statecode 값 -> 표출 라벨 매핑
const STATE_CODE_LABELS: Record<number, string> = {
  0: 'Unknown',
  1: 'PoweredOff',
  2: 'Initializing',
  3: 'Idle',
  4: 'Sitting',
  5: 'Standing',
  6: 'Moving',
  7: 'Recovering',
  8: 'Error'
};

// 로봇 정보 클래스 선언
export interface RobotInfo {
  id: string;
  robot_ip: string;
  robot_port: number;
  isOnline: boolean;
  statusLabel: string;
  battery: number;
  mode: string;
  voiceOn: boolean;
  currentMap: string;
  uptime: string;
}

export function useRobotInfo() {
  const robotInfo = ref<RobotInfo | null>(null);
  const isLoading = ref<boolean>(false);
  let metricsTimer: ReturnType<typeof setInterval> | null = null;
  const robotStore = useRobotStore();
  const { robots } = storeToRefs(robotStore);

  const fetchRobotInfo = async () => {
    try {
      // 기본(로컬) 상세값
      const mockDetail: RobotInfo = {
        id: '',
        robot_ip: '',
        robot_port: 0,
        isOnline: false,
        statusLabel: STATE_CODE_LABELS[0],
        battery: 0,
        mode: '',
        voiceOn: false,
        currentMap: '',
        uptime: ''
      };

      const main = robots.value.find(r => r.isMain === true);
      if (main && main.telemetry) {
        mockDetail.id = main.id ?? mockDetail.id;
        mockDetail.robot_ip = main.robot_ip ?? mockDetail.robot_ip;
        mockDetail.robot_port = main.robot_port ?? mockDetail.robot_port;
        mockDetail.isOnline = main.telemetry.isOnline ?? mockDetail.isOnline;
        mockDetail.statusLabel = STATE_CODE_LABELS[main.telemetry.statecode ?? 0] ?? STATE_CODE_LABELS[0];
        mockDetail.battery = main.telemetry.battery ?? mockDetail.battery;
        mockDetail.mode = main.telemetry.isManual ? 'MANUAL' : (main.telemetry.locomotionMode ? 'AUTO' : mockDetail.mode);
        mockDetail.voiceOn = main.telemetry.isVoiceActive ?? mockDetail.voiceOn;
        mockDetail.currentMap = main.telemetry.currentMap ?? mockDetail.currentMap;
        mockDetail.uptime = main.telemetry.uptime ?? mockDetail.uptime;
        robotInfo.value = mockDetail;
      } else {
        robotInfo.value = null;
      }

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