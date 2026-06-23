import { ref, watch, onUnmounted, Ref } from 'vue'

const LOG_PREFIX = '[CameraStream]'
const STAT_INTERVAL_MS = 10_000

export function useCameraStream(slots: Ref<Array<any>>) {
  const ws_clients = ref<Array<WebSocket | null>>(new Array(6).fill(null))

  // 그리드용 캔버스 (슬롯별)
  const _canvases = new Array<HTMLCanvasElement | null>(6).fill(null)
  // 모달용 캔버스 (열린 슬롯 하나만)
  let _modalCanvasSlot: number | null = null
  let _modalCanvas: HTMLCanvasElement | null = null

  const _latestBitmaps = new Array<ImageBitmap | null>(6).fill(null)
  const _rafScheduled = new Array<boolean>(6).fill(false)
  // 같은 커넥션 내 out-of-order 프레임 폐기용 시퀀스
  const _frameSeqs = new Array<number>(6).fill(0)

  const _frameCount = new Array(6).fill(0)
  const _lastStatTime = new Array(6).fill(0)
  const _reconnectCount = new Array(6).fill(0)
  const _statTimers = new Array<ReturnType<typeof setInterval> | null>(6).fill(null)
  const _reconnectTimers = new Array<ReturnType<typeof setTimeout> | null>(6).fill(null)
  let _mounted = true

  function _drawToCanvas(canvas: HTMLCanvasElement | null, bitmap: ImageBitmap) {
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    if (canvas.width !== bitmap.width) canvas.width = bitmap.width
    if (canvas.height !== bitmap.height) canvas.height = bitmap.height
    ctx.drawImage(bitmap, 0, 0)
  }

  // 모달용: CSS 크기로 캔버스를 채우고, 비율을 유지하며 중앙에 그림 (object-fit:contain)
  function _drawToCanvasContain(canvas: HTMLCanvasElement | null, bitmap: ImageBitmap) {
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const { width: cw, height: ch } = canvas.getBoundingClientRect()
    const w = cw || bitmap.width
    const h = ch || bitmap.height
    if (canvas.width !== w) canvas.width = w
    if (canvas.height !== h) canvas.height = h
    const scale = Math.min(w / bitmap.width, h / bitmap.height)
    const dw = bitmap.width * scale
    const dh = bitmap.height * scale
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, w, h)
    ctx.drawImage(bitmap, (w - dw) / 2, (h - dh) / 2, dw, dh)
  }

  function _drawFrame(idx: number) {
    _rafScheduled[idx] = false
    const bitmap = _latestBitmaps[idx]
    if (!bitmap) return
    _drawToCanvas(_canvases[idx], bitmap)
    if (_modalCanvasSlot === idx) _drawToCanvasContain(_modalCanvas, bitmap)
  }

  function _scheduleRaf(idx: number) {
    if (_rafScheduled[idx]) return
    _rafScheduled[idx] = true
    requestAnimationFrame(() => _drawFrame(idx))
  }

  // 템플릿에서 <canvas :ref="(el) => setCanvas(idx, el as HTMLCanvasElement | null)"> 형태로 등록
  function setCanvas(idx: number, el: HTMLCanvasElement | null) {
    _canvases[idx] = el
    if (el) {
      const bitmap = _latestBitmaps[idx]
      if (bitmap) _drawToCanvas(el, bitmap)
    }
  }

  // 모달 캔버스 등록/해제. 컴포넌트에서 mount/unmount 시점에 호출.
  function setModalCanvas(idx: number | null, el: HTMLCanvasElement | null) {
    _modalCanvasSlot = idx
    _modalCanvas = el
    if (idx !== null && el) {
      const bitmap = _latestBitmaps[idx]
      if (bitmap) _drawToCanvasContain(el, bitmap)
    }
  }

  function _clearCanvas(idx: number) {
    const canvas = _canvases[idx]
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    _latestBitmaps[idx]?.close()
    _latestBitmaps[idx] = null
  }

  function _startStatTimer(idx: number) {
    if (_statTimers[idx]) clearInterval(_statTimers[idx]!)
    _lastStatTime[idx] = Date.now()
    _frameCount[idx] = 0
    _statTimers[idx] = setInterval(() => {
      const ws = ws_clients.value[idx]
      const state = ws ? ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][ws.readyState] : 'NULL'
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
    _frameSeqs[idx] = 0
    console.info(
      `${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 시도 (재연결 횟수: ${_reconnectCount[idx]}회) - URL: ${streamUrl}`
    )

    try {
      const ws = new WebSocket(streamUrl, 'camera-stream')
      ws.binaryType = 'arraybuffer'
      ws_clients.value[idx] = ws

      ws.onopen = () => {
        console.info(`${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 성공 - readyState: OPEN`)
        _startStatTimer(idx)
      }

      ws.onmessage = async (event) => {
        if (!(event.data instanceof ArrayBuffer)) return
        const buffer = event.data
        if (buffer.byteLength <= 24) {
          console.warn(`${LOG_PREFIX} [Slot ${idx}] 수신 데이터 크기 이상 (${buffer.byteLength}bytes <= 24bytes 헤더)`)
          return
        }

        _frameCount[idx]++
        const mySeq = ++_frameSeqs[idx]

        const blob = new Blob([buffer.slice(24)], { type: 'image/jpeg' })
        let bitmap: ImageBitmap
        try {
          bitmap = await createImageBitmap(blob)
        } catch (e) {
          console.warn(`${LOG_PREFIX} [Slot ${idx}] ImageBitmap 생성 실패:`, e)
          return
        }

        // 커넥션이 교체됐거나 더 최신 프레임이 먼저 디코딩된 경우 폐기
        if (ws_clients.value[idx] !== ws || mySeq < _frameSeqs[idx]) {
          bitmap.close()
          return
        }

        _latestBitmaps[idx]?.close()
        _latestBitmaps[idx] = bitmap
        _scheduleRaf(idx)
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
        if (ws_clients.value[idx] === ws) ws_clients.value[idx] = null
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

    if (_reconnectTimers[idx]) {
      clearTimeout(_reconnectTimers[idx]!)
      _reconnectTimers[idx] = null
    }

    const ws = ws_clients.value[idx]
    if (ws) {
      console.info(`${LOG_PREFIX} [Slot ${idx}] WebSocket 연결 종료 요청 (readyState: ${ws.readyState})`)
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      ws.close()
      ws_clients.value[idx] = null
    }

    _clearCanvas(idx)
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
    if (document.visibilityState === 'visible') resumeMissingStreams()
  }
  document.addEventListener('visibilitychange', visibilityHandler)

  onUnmounted(() => {
    _mounted = false
    for (let i = 0; i < 6; i++) stopJpgStream(i)
    document.removeEventListener('visibilitychange', visibilityHandler)
  })

  return { setCanvas, setModalCanvas }
}
