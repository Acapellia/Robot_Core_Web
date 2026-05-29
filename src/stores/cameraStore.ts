import { defineStore } from 'pinia';
import { ref } from 'vue';

// ==========================================
// 1. 타입 정의 및 설정값
// ==========================================
export interface CameraItem {
    id: string;
    name: string;
    url: string;
    username?: string;
    password?: string;
    streamUrl?: string | null;
    slot: number | null;
}

// 스트림 검증 관련 설정
const STREAM_VALIDATION = {
    maxAttempts: 3,       // 최대 재시도 횟수
    attemptDelayMs: 500,  // 재시도 사이의 간격 (0.5초)
    timeoutMs: 5000,      // 웹소켓 연결 타임아웃 (5초)
};

export const useCameraStore = defineStore('camera', () => {
    // 상태 관리 (등록된 카메라 목록)
    const cameras = ref<CameraItem[]>([]);


    // ==========================================
    // 3. 핵심 비즈니스 로직 함수 (분리됨)
    // ==========================================

    // NOTE: Stream validation moved to server-side (BroadcastManager / CameraStreamManager).

    /**
     * [단계 1] 백엔드에 카메라 연결을 요청하고 스트림 URL을 받아옵니다.
     */
    function requestCameraConnect(payload: Omit<CameraItem, 'id' | 'slot' | 'streamUrl'>): Promise<{ streamUrl: string; slot: number }> {
        return new Promise((resolve, reject) => {
            const hostname = 'localhost';
            const ws_url = `ws://${hostname}:8000/ws/camera_control`;

            const ws = new WebSocket(ws_url);

            ws.onopen = () => {
                ws.send(JSON.stringify({
                    type: 'camera_connect',
                    url: payload.url,
                    username: payload.username,
                    password: payload.password,
                    slot: null // 백엔드가 자동으로 슬롯을 할당하도록 설정
                }));
            };

            ws.onmessage = (event) => {
                // clearTimeout(timer);
                ws.close();

                try {
                    const res = JSON.parse(event.data);
                    console.log('[Camera] Camera control response:', res);
                    if (res.type === 'camera_connected' && res.streamUrl) {
                        resolve({ streamUrl: res.streamUrl, slot: res.slot });
                    } 
                    else if (res.type === 'camera_connect_fail') {
                        const reason = res.reason || '카메라 연결 실패 (서버에서 실패 응답)';
                        reject(new Error(reason));
                    } else {
                        reject(new Error('카메라 연결 실패 (백엔드 에러 반환)'));
                    }
                } catch (err) {
                    reject(new Error('서버 응답 데이터 파싱 실패'));
                }
            };

            ws.onerror = (err) => {
                reject(err);
            };
        });
    }

    /**
     * [메인 함수] 카메라를 최종 등록합니다.
     * 외부(컴포넌트)에서는 이 함수만 호출하면 됩니다.
     */
    async function addCamera(payload: Omit<CameraItem, 'id' | 'slot' | 'streamUrl'>): Promise<CameraItem> {
        // 1단계: 백엔드에 카메라 연결 요청하여 스트림 URL 받아오기
        const { streamUrl, slot } = await requestCameraConnect(payload);

        // 2단계: 스트림 검증은 서버(BroadcastManager)에서 수행합니다.
        // 서버가 성공 응답을 보냈으므로 클라이언트에서는 추가 검증을 생략합니다.

        // 3단계: 검증이 완료되면 스토어 상태(State)에 추가하기
        const newCamera: CameraItem = {
            id: Math.random().toString(36).substring(2, 9), // 랜덤 ID 생성
            name: payload.name,
            url: payload.url,
            username: payload.username,
            password: payload.password,
            slot: slot,
            streamUrl: streamUrl
        };

        cameras.value.push(newCamera);
        return newCamera;
    }

    return { cameras, addCamera };
});