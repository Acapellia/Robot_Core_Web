import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface CameraItem {
    id: string;
    name: string;
    url: string;
    username?: string;
    password?: string;
    streamUrl?: string | null;
    slot: number | null;
}

export const STREAM_VALIDATION = {
    maxAttempts: 3,
    attemptDelayMs: 500,
    attemptTimeoutMs: 5000,
};

export const useCameraStore = defineStore('camera', () => {
    const cameras = ref<CameraItem[]>([]);

    function getApiBase() {
        const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL;
        if (envBase) return envBase.replace(/\/$/, '');
        return `${window.location.protocol}//${window.location.hostname}:8000`;
    }

    function makeWsUrl() {
        const base = getApiBase();
        return base.replace(/^http/, 'ws') + '/ws/camera_control';
    }

    function addCamera(payload: Omit<CameraItem, 'id' | 'slot' | 'streamUrl'>) {
        return new Promise<CameraItem>((resolve, reject) => {
            const wsUrl = makeWsUrl();
            const ws = new WebSocket(wsUrl);

            const timer = setTimeout(() => {
                ws.close();
                reject(new Error('카메라 제어 웹소켓 타임아웃'));
            }, STREAM_VALIDATION.attemptTimeoutMs);

            ws.onopen = () => {
                ws.send(JSON.stringify({
                    type: 'camera_connect',
                    url: payload.url,
                    username: payload.username,
                    password: payload.password,
                    slot: null // 백엔드 자동 할당 유도
                }));
            };

            ws.onmessage = (event) => {
                clearTimeout(timer);
                try {
                    const res = JSON.parse(event.data);
                    if (res.type === 'camera_connected') {
                        const streamUrl: string | undefined = res.streamUrl;

                        if (!streamUrl) {
                            reject(new Error('스트림 URL이 제공되지 않았습니다.'));
                            ws.close();
                            return;
                        }

                        // 스트림에 대해 여러 번(최대 10회) 시도하여 첫 유효 프레임을 받을 때까지 대기
                        const maxAttempts = STREAM_VALIDATION.maxAttempts;
                        const attemptDelayMs = STREAM_VALIDATION.attemptDelayMs;

                        const tryStreamWithRetries = (): Promise<void> => {
                            return new Promise((resok, rej) => {
                                let attempts = 0;
                                let stopped = false;
                                let pendingTimer: ReturnType<typeof setTimeout> | null = null;

                                const clearPending = () => {
                                    if (pendingTimer) {
                                        clearTimeout(pendingTimer as any);
                                        pendingTimer = null;
                                    }
                                };

                                const tryOnce = () => {
                                    if (stopped) return;
                                    attempts += 1;
                                    let testWs: WebSocket | null = null;

                                    const attemptTimer = setTimeout(() => {
                                        try { testWs && testWs.close(); } catch (_) {}
                                        testWs = null;
                                        if (attempts >= maxAttempts) {
                                            stopped = true;
                                            rej(new Error(`스트림 연결 실패 (${maxAttempts}회 시도)`));
                                        } else {
                                            pendingTimer = setTimeout(tryOnce, attemptDelayMs);
                                        }
                                    }, STREAM_VALIDATION.attemptTimeoutMs);

                                    try {
                                        testWs = new WebSocket(streamUrl);
                                        testWs.binaryType = 'arraybuffer';

                                        testWs.onmessage = (evt) => {
                                            const data = evt.data;
                                            if (!(data instanceof ArrayBuffer)) return;
                                            if (data.byteLength <= 24) return;

                                            clearTimeout(attemptTimer);
                                            try { testWs && testWs.close(); } catch (_) {}
                                            testWs = null;
                                            stopped = true;
                                            clearPending();
                                            resok();
                                        };

                                        testWs.onerror = () => {
                                            clearTimeout(attemptTimer);
                                            try { testWs && testWs.close(); } catch (_) {}
                                            testWs = null;
                                            if (attempts >= maxAttempts) {
                                                stopped = true;
                                                clearPending();
                                                rej(new Error(`스트림 연결 오류 (${maxAttempts}회 시도)`));
                                            } else {
                                                pendingTimer = setTimeout(tryOnce, attemptDelayMs);
                                            }
                                        };
                                    } catch (err) {
                                        clearTimeout(attemptTimer);
                                        try { testWs && testWs.close(); } catch (_) {}
                                        testWs = null;
                                        if (attempts >= maxAttempts) {
                                            stopped = true;
                                            clearPending();
                                            rej(err as any);
                                        } else {
                                            pendingTimer = setTimeout(tryOnce, attemptDelayMs);
                                        }
                                    }
                                };

                                tryOnce();
                            });
                        };

                        tryStreamWithRetries().then(() => {
                            const newCam: CameraItem = {
                                id: Math.random().toString(36).substring(2, 9),
                                name: payload.name,
                                url: payload.url,
                                username: payload.username,
                                password: payload.password,
                                slot: res.slot,
                                streamUrl: streamUrl
                            };
                            cameras.value.push(newCam);
                            resolve(newCam);
                        }).catch((err) => {
                            reject(err);
                        }).finally(() => {
                            ws.close();
                        });
                    } else {
                        reject(new Error('연결 실패 반환'));
                    }
                } catch (e) {
                    reject(e);
                }
                ws.close();
            };

            ws.onerror = (err) => {
                clearTimeout(timer);
                reject(err);
            };
        });
    }

    return { cameras, addCamera };
});