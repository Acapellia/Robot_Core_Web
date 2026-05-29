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

export const useCameraStore = defineStore('camera', () => {
    // 상태 관리 (등록된 카메라 목록)
    const cameras = ref<CameraItem[]>([]);

    // ==========================================
    // 2. 카메라 등록 로직
    // ==========================================
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
        // 백엔드에 카메라 연결 요청하여 스트림 URL 받아오기
        const { streamUrl, slot } = await requestCameraConnect(payload);

        // 스토어 상태(State)에 추가하기
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