import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface Hub {
  ip: string;
  port: string;
}

export const useHubStore = defineStore('hub', () => {
  const hubs = ref<Hub[]>([]);
  const selectedHubId = ref<string | null>(null);
  let ws: WebSocket | null = null;
  const wsConnected = ref(false);
  const errorMsg = ref<string | null>(null);
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

    const hostname = 'localhost';
    const wsUrl = `ws://${hostname}:8000/ws/control`;

    console.info('[hubStore] connectWebSocket() 시도 ->', wsUrl);

    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      console.error('[hubStore] WebSocket 생성 실패', e);
      errorMsg.value = `WebSocket 생성 실패: ${e}`;
      wsConnected.value = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWebSocket, 3000);
      return;
    }

    ws.onopen = () => {
      wsConnected.value = true;
      errorMsg.value = null;
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    };

    ws.onclose = (ev) => {
      wsConnected.value = false;
      errorMsg.value = '브로드캐스트 매니저와의 연결이 끊어졌습니다.';
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (ev) => {
      wsConnected.value = false;
      errorMsg.value = '브로드캐스트 매니저 연결 에러';
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        // 2. [수신] 중계기가 언제든 연결에 성공하면 리스트에 추가하고 표출
        if (msg.payload && msg.payload.type === 'HUB_CONNECTED') {
          const hub = msg.payload.hub;
          
          if (hub.ip && hub.port) {
            // 중복 검사 후 리스트 등록
            if (!hubs.value.some(h => h.ip === hub.ip && h.port === hub.port)) {
              hubs.value.push({ ip: hub.ip, port: hub.port });
              
              // 첫 허브라면 자동 선택
              if (hubs.value.length === 1) {
                selectedHubId.value = hub.ip;
              }
            }
          }
        }
        // 서버가 현재 등록된 허브 목록을 초기 전송해 올 경우 처리
        else if (msg.payload && msg.payload.type === 'CURRENT_HUBS') {
          const list = msg.payload.hubs || [];
          if (Array.isArray(list)) {
            list.forEach((hub: any) => {
              if (hub.ip && hub.port && !hubs.value.some(h => h.ip === hub.ip && h.port === hub.port)) {
                hubs.value.push({ ip: hub.ip, port: hub.port });
              }
            });

            if (!selectedHubId.value && hubs.value.length > 0) {
              selectedHubId.value = hubs.value[0].ip;
            }
          }
        }
      } catch (e) {
        console.debug('[hubStore] 메시지 파싱 실패', e);
      }
    };
  }

  // 1. [요청] 허브 추가 버튼 눌렀을 때 사용될 허브 연결 요청 기능
  function connectHub(ip: string, port: string) {
    const payload = JSON.stringify({
      type: 'robot_hub_connect',
      ip,
      port,
      handshake:  "header: { source: 'WEB_UI', client: 'robot_core_web' }"
    });

    if (ws && ws.readyState === WebSocket.OPEN) {
      console.info('[Connect] robot_hub_connect 전송 ->', ip, port);
      ws.send(payload);
      return;
    }

    console.warn('[hubStore] WebSocket이 열려있지 않습니다. 브로드캐스트 매니저에 연결 중입니다. 잠시 후 다시 시도해주세요.');
    errorMsg.value = '브로드캐스트 매니저에 연결되어 있지 않습니다. 새로고침 또는 다시 시도하세요.';
    // 자동 재전송은 스토어에서 수행하지 않습니다. 수동으로 재시도하려면 UI에서 다시 호출해주세요.
    connectWebSocket();
  }

  function selectHub(id: string) {
    selectedHubId.value = id;
  }

  connectWebSocket();

  return {
    hubs,
    selectedHubId,
    wsConnected,
    errorMsg,
    connectWebSocket,
    connectHub,
    selectHub
  };
});