import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface VAEngine {
  ip: string;
  port: string;
  id?: string;
  pw?: string;
}

export const useVAStore = defineStore('va', () => {
  const vaEngines = ref<VAEngine[]>([]);
  const selectedVAEngineIP = ref<string | null>(null);
  let ws: WebSocket | null = null;
  const wsConnected = ref(false);
  const errorMsg = ref<string | null>(null);
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

    const hostname = window.location.hostname || 'localhost';
    const wsUrl = `ws://${hostname}:8000/ws/control`;

    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      console.error('[vaStore] WebSocket 생성 실패', e);
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

    ws.onclose = () => {
      wsConnected.value = false;
      errorMsg.value = '브로드캐스트 매니저와의 연결이 끊어졌습니다.';
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
      wsConnected.value = false;
      errorMsg.value = '브로드캐스트 매니저 연결 에러';
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.payload && msg.payload.type === 'VA_CONNECTED') {
          const va = msg.payload.va;
          if (va && va.ip && va.port) {
            if (!vaEngines.value.some(v => v.ip === va.ip && v.port === va.port)) {
              vaEngines.value.push({ ip: va.ip, port: va.port, id: va.id, pw: undefined });
              if (!selectedVAEngineIP.value) selectedVAEngineIP.value = va.ip;
            }
          }
        } else if (msg.payload && msg.payload.type === 'CURRENT_VAS') {
          const list = msg.payload.vas || [];
          if (Array.isArray(list)) {
            list.forEach((va: any) => {
              if (va.ip && va.port && !vaEngines.value.some(v => v.ip === va.ip && v.port === va.port)) {
                vaEngines.value.push({ ip: va.ip, port: va.port, id: va.id, pw: undefined });
              }
            });

            if (!selectedVAEngineIP.value && vaEngines.value.length > 0) {
              selectedVAEngineIP.value = vaEngines.value[0].ip;
            }
          }
        }
      } catch (e) {
        console.debug('[vaStore] 메시지 파싱 실패', e);
      }
    };
  }

  function connectVA(ip: string, port: string, id: string, pw: string) {
    const payload = JSON.stringify({
      type: 'connect-va',
      ip,
      port,
      auth: { id, pw },
      handshake: { header: { source: 'WEB_UI', client: 'robot_core_ui' } }
    });

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(payload);
      return;
    }

    errorMsg.value = '브로드캐스트 매니저에 연결되어 있지 않습니다. 잠시 후 다시 시도하세요.';
    connectWebSocket();
  }

  function selectVA(ip: string) {
    selectedVAEngineIP.value = ip;
  }

  connectWebSocket();

  return {
    vaEngines,
    selectedVAEngineIP,
    wsConnected,
    errorMsg,
    connectWebSocket,
    connectVA,
    selectVA
  };
});
