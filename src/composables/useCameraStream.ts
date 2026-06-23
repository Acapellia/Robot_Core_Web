import { ref, watch, onUnmounted, computed, Ref } from 'vue'

const LOG_PREFIX = '[CameraStream]'
const STAT_INTERVAL_MS = 10_000

export function useCameraStream(slots: Ref<Array<any>>) {
  const blob_urls = ref<Array<string | null>>(new Array(6).fill(null))
  const ws_clients = ref<Array<WebSocket | null>>(new Array(6).fill(null))

  // 진단용 통계
  const _frameCount = new Array(6).fill(0)
  const _lastStatTime = new Array(6).fill(0)
  const _reconnectCount = new Array(6).fill(0)
  const _statTimers = new Array<ReturnType<typeof setInterval> | null>(6).fill(null)
  const _reconnectTimers = new Array<ReturnType<typeof setTimeout> | null>(6).fill(null)
  let _mounted = true

  function _startStatTimer(idx: number) {
    if (_statTimers[idx]) clearInterval(_statTimers[idx]!)
    _lastStatTime[idx] = Date.now()
    _frameCount[idx] = 0
    _statTimers[idx] = setInterval(() => {
      const ws = ws_clients.value[idx]
      const state = ws ? ['CONNECTING','OPEN','CLOSING','CLOSED'][ws.readyState] : 'NULL'
      const elapsed = (Date.now() - _lastStatTime[idx]) / 1000
      const fps = elapsed > 0 ? (_frameCount[idx] / elapsed).toFixed(1) : '0.0'
      console.info(
        `${LOG_PREFIX} [Slot ${idx}] [통계] FPS: ${fps}, ` +
        `수신 프레임(구간): ${_frameCount[idx]}장, ` +
        `WebSocket 상태: ${state}, ` +
        `재연결 횟수: ${_reconnectCount[idx]}회`
      )
      _frameCount[idx] = 0
      _lastStatTime[idx] = Date.now()
    }, STAT_INTERVAL_MS)
  }

  function _stopStatTimer(idx: number) {
    if (_statTimers[idx]) {
      clearInterval(_statTimers[idx]!)
      _statTimers[idx] = null
    }
  }

  function startJpgStream(idx: number, streamUrl: string) {
    stopJpgStream(idx)
    _reconnectCount[idx]++
    console.info(
      `${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 시도 (재연결 횟수: ${_reconnectCount[idx]}회) - URL: ${streamUrl}`
    )

    try {
      const ws = new WebSocket(streamUrl, "camera-stream")
      ws.binaryType = 'arraybuffer'
      ws_clients.value[idx] = ws

      ws.onopen = () => {
        console.info(`${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 성공 - readyState: OPEN`)
        _startStatTimer(idx)
      }

      ws.onmessage = (event) => {
        if (!(event.data instanceof ArrayBuffer)) return
        const buffer = event.data
        if (buffer.byteLength <= 24) {
          console.warn(`${LOG_PREFIX} [Slot ${idx}] 수신 데이터 크기 이상 (${buffer.byteLength}bytes <= 24bytes 헤더)`)
          return
        }

        _frameCount[idx]++

        const imagePayload = buffer.slice(24)
        const blob = new Blob([imagePayload], { type: 'image/jpeg' })
        const newUrl = URL.createObjectURL(blob)

        // 새 URL을 먼저 설정한 뒤 이전 URL을 revoke — 교체 순간 빈 화면 방지
        const oldUrl = blob_urls.value[idx]
        blob_urls.value[idx] = newUrl
        if (oldUrl) URL.revokeObjectURL(oldUrl)
      }

      ws.onerror = (event) => {
        console.error(`${LOG_PREFIX} [Slot ${idx}] WebSocket 에러 발생:`, event)
      }

      ws.onclose = (event) => {
        _stopStatTimer(idx)
        const reason = event.reason ? ` reason: "${event.reason}"` : ''
        const wasClean = event.wasClean ? '정상 종료' : '비정상 종료'
        console.warn(
          `${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 종료 - ` +
          `${wasClean}, code: ${event.code}${reason}`
        )
        if (ws_clients.value[idx] === ws) {
          ws_clients.value[idx] = null
        }
        // 컴포넌트가 이미 언마운트된 경우 재연결 시도하지 않음
        if (!_mounted) return
        _reconnectTimers[idx] = setTimeout(() => {
          _reconnectTimers[idx] = null
          if (!_mounted) return
          const currentCam = slots.value[idx]
          if (currentCam && currentCam.streamUrl && ws_clients.value[idx] === null) {
            console.info(`${LOG_PREFIX} [Slot ${idx}] 2초 대기 후 재연결 시도`)
            startJpgStream(idx, currentCam.streamUrl)
          }
        }, 2000)
      }
    } catch (err) {
      console.error(`${LOG_PREFIX} [Slot ${idx}] WebSocket 생성 에러:`, err)
    }
  }

  function stopJpgStream(idx: number) {
    _stopStatTimer(idx)

    // 대기 중인 재연결 타이머를 먼저 취소해서 유령 연결 방지
    if (_reconnectTimers[idx]) {
      clearTimeout(_reconnectTimers[idx]!)
      _reconnectTimers[idx] = null
    }

    const ws = ws_clients.value[idx]
    if (ws) {
      console.info(`${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 종료 요청 (readyState: ${ws.readyState})`)
      // 핸들러를 먼저 null로 만들어 onclose의 자동 재연결 타이머가 등록되지 않게 차단
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      ws.close()
      ws_clients.value[idx] = null
    }
    if (blob_urls.value[idx]) {
      URL.revokeObjectURL(blob_urls.value[idx]!)
      blob_urls.value[idx] = null
    }
  }

  function resumeMissingStreams() {
    for (let i = 0; i < 6; i++) {
      const cam = slots.value[i]
      if (cam && cam.streamUrl) {
        const ws = ws_clients.value[i]
        const isAlive = ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)
        if (!isAlive) {
          console.warn(`${LOG_PREFIX} [Slot ${i}] 탭 복귀 감지 - 스트림 복구 시도 (현재 상태: ${ws ? ws.readyState : 'null'})`)
          startJpgStream(i, cam.streamUrl)
        }
      }
    }
  }

  watch(slots, (newSlots) => {
    for (let i = 0; i < 6; i++) {
      const cam = newSlots[i]
      if (cam && cam.streamUrl) {
        if (!ws_clients.value[i] || ws_clients.value[i]?.url !== cam.streamUrl) {
          startJpgStream(i, cam.streamUrl)
        }
      } else {
        stopJpgStream(i)
      }
    }
  }, { immediate: true, deep: true })

  const visibilityHandler = () => {
    if (document.visibilityState === 'visible') {
      resumeMissingStreams()
    }
  }

  document.addEventListener('visibilitychange', visibilityHandler)

  onUnmounted(() => {
    _mounted = false
    for (let i = 0; i < 6; i++) {
      stopJpgStream(i)
    }
    document.removeEventListener('visibilitychange', visibilityHandler)
  })

  return {
    blob_urls: computed(() => blob_urls.value)
  }
}