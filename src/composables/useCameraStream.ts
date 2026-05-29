import { ref, watch, onUnmounted, computed, Ref } from 'vue'

export function useCameraStream(slots: Ref<Array<any>>) {
  const blob_urls = ref<Array<string | null>>(new Array(6).fill(null))
  const ws_clients = ref<Array<WebSocket | null>>(new Array(6).fill(null))

  function startJpgStream(idx: number, streamUrl: string) {
    stopJpgStream(idx)

    try {
      const ws = new WebSocket(streamUrl)
      ws.binaryType = 'arraybuffer'
      ws_clients.value[idx] = ws

      ws.onmessage = (event) => {
        if (!(event.data instanceof ArrayBuffer)) return
        const buffer = event.data
        if (buffer.byteLength <= 24) return

        const imagePayload = buffer.slice(24)
        const blob = new Blob([imagePayload], { type: 'image/jpeg' })

        if (blob_urls.value[idx]) {
          URL.revokeObjectURL(blob_urls.value[idx]!)
        }

        blob_urls.value[idx] = URL.createObjectURL(blob)
      }

      ws.onclose = () => {
        setTimeout(() => {
          const currentCam = slots.value[idx]
          if (currentCam && currentCam.streamUrl && ws_clients.value[idx] === null) {
            startJpgStream(idx, currentCam.streamUrl)
          }
        }, 2000)
      }
    } catch (err) {
      console.error(`[Slot ${idx}] Composable 웹소켓 스트림 연동 에러:`, err)
    }
  }

  function stopJpgStream(idx: number) {
    if (ws_clients.value[idx]) {
      ws_clients.value[idx].close()
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
        if (!ws_clients.value[i]) {
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
    for (let i = 0; i < 6; i++) {
      stopJpgStream(i)
    }
    document.removeEventListener('visibilitychange', visibilityHandler)
  })

  return {
    blob_urls: computed(() => blob_urls.value)
  }
}