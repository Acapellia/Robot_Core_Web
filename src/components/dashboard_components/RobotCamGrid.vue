<template>
  <div class="top-grid">
    <div 
      v-for="(cam, idx) in slots" 
      :key="idx" 
      class="card" 
      :class="{ 'has-cam': cam }"
      @dblclick="cam ? openPopup(idx) : null"
    >
      <div class="tile-header">{{ cam ? cam.name : `Camera ${idx + 1}` }}</div>
      <div class="tile-body">
        <img v-if="cam && blob_urls[idx]" :src="blob_urls[idx]!" class="live-img" />
        <div v-else class="placeholder">No stream</div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="selectedIdx !== null" class="modal-overlay" @click.self="closePopup">
        
        <div class="modal-premium-frame">
          
          <div class="frame-unified-container">
            
            <div class="frame-nested-title">
              <span class="pulse-dot"></span>
              <span class="title-text">{{ slots[selectedIdx]?.name || `Camera ${selectedIdx + 1}` }}</span>
            </div>

            <button class="frame-nested-close-btn" @click="closePopup">
              ✕ 닫기
            </button>

            <div class="premium-screen-box">
              <img 
                v-if="blob_urls[selectedIdx]" 
                :src="blob_urls[selectedIdx]!" 
                class="modal-live-img" 
              />
              <div v-else class="modal-placeholder">No stream</div>
            </div>

          </div>

        </div>

      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCameraStore } from '../../stores/cameraStore'
import { useCameraStream } from '../../composables/useCameraStream'

const store = useCameraStore()

const slots = computed(() => {
  const out: Array<any> = new Array(6).fill(null)
  const cams = (store.cameras ?? []) as any[]
  for (let i = 0; i < Math.min(cams.length, 6); i++) {
    out[i] = cams[i]
  }
  return out
})

const { blob_urls } = useCameraStream(slots)
const selectedIdx = ref<number | null>(null)

function openPopup(idx: number) {
  selectedIdx.value = idx
}

function closePopup() {
  selectedIdx.value = null
}
</script>

<style scoped>
/* ==========================================================================
   [1] 메인 대시보드 오리지널 카드 슬롯 스타일 (보존)
   ========================================================================== */
.top-grid { height: 100%; display:grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 1fr; gap: 12px; }
.card {
  height: 100%;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
  overflow: hidden;
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card.has-cam { cursor: pointer; }
.card.has-cam:hover { transform: scale(1.01); box-shadow: 0 6px 16px rgba(13, 27, 34, 0.1); }

.tile-header { position: absolute; top: 8px; left: 8px; z-index: 3; background: rgba(255,255,255,0.9); padding: 4px 8px; border-radius: 8px; font-weight:700; color:#233; font-size:13px }
.tile-body { position: absolute; inset: 0; padding-top: 36px; background: #000 }
.live-img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; z-index:0 }
.placeholder { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,#000,#0b0b0b); background-color:#000; color:#9aa; font-weight:600; z-index:1 }


/* ==========================================================================
   [2] 🌟 영상 스크린 실선 보더 디테일이 추가된 프리미엄 와이드 모달 스타일
   ========================================================================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(24, 32, 43, 0.35);
  backdrop-filter: blur(16px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

/* 반투명 크리스탈 화이트 바탕 + 파스텔 연보라 입체 더블 섀도우 */
.modal-premium-frame {
  width: 92vw;
  max-width: 1500px;
  height: 68vh;
  padding: 7px;
  background: linear-gradient(135deg, #d3c4fc 0%, #badaff 50%, #eadaff 100%);
  border-radius: 24px;
  box-shadow: 
    0 4px 24px rgba(153, 129, 235, 0.15), 
    0 24px 64px rgba(33, 44, 61, 0.28); 
  display: flex;
}

/* 내부 바디 판넬 */
.frame-unified-container {
  flex: 1;
  position: relative;
  padding: 16px; 
  padding-top: 56px; /* 이름표/단추 수용 공간 고수 */
  background: rgba(255, 255, 255, 0.94); 
  border-radius: 22px;
  display: flex;
  flex-direction: column;
}

/* 이름표 스타일 */
.frame-nested-title {
  position: absolute;
  top: 15px;
  left: 18px;
  z-index: 5;
  background: #eaf4ff; 
  border: 1px solid #b8daff;
  padding: 4px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.title-text { font-weight: 700; color: #2e4d77; font-size: 12.5px; }
.pulse-dot { width: 6px; height: 6px; background-color: #aa95f7; border-radius: 50%; }

/* 닫기 버튼 스타일 */
.frame-nested-close-btn {
  position: absolute;
  top: 15px;
  right: 18px;
  z-index: 5;
  background: #f3f0ff; 
  color: #6a57b7;
  border: 1px solid #ded5ff;
  padding: 4px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}
.frame-nested-close-btn:hover {
  background: #e9e2ff;
  border-color: #bfaeff;
  color: #4a3799;
}

/* ── 🌟 [중앙 비디오 구역] 디테일 경계선 주입 ── */
.premium-screen-box {
  flex: 1;
  background: #0b0f15; 
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 🎨 [변경] 투명도 없는 맑은 밀크 파란색 실선으로 두께를 5px까지 키워 확실하게 선을 긋습니다 */
  border: 5px solid #b2d5ff; 
  
  /* 🎨 [추가] 테두리 선 바깥쪽으로 부드러운 파스텔 블루 후광을 주어 선이 더욱 선명하게 돋보이도록 처리 */
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.2),
    0 0 12px rgba(178, 213, 255, 0.4); 
}

.modal-live-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.modal-placeholder { color: #414f64; font-size: 13px; font-weight: 600; }
</style>