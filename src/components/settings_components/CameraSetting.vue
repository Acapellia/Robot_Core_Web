<template>
  <div v-if="topMessage" class="top-popup">{{ topMessage }}</div>
  <div class="camera-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        CAMERA MANAGEMENT
      </h3>
      <span class="linked-info">
        Linked to: <span class="highlight">{{ selectedCameraName || 'None' }}</span>
      </span>
    </div>

    <div class="body-zone">
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group name-group">
            <label>CAMERA NAME</label>
            <input type="text" v-model="newCamera.name" placeholder="Enter name..." />
          </div>
          <div class="form-group" style="grid-column: span 2;">
            <label>CAMERA URL</label>
            <input type="text" v-model="newCamera.url" placeholder="Enter CAMERA URL..." />
          </div>
          <div class="form-group">
            <label>CAMERA ID</label>
            <input type="text" v-model="newCamera.username" placeholder="Enter CAMERA ID..." />
          </div>
          <div class="form-group">
            <label>CAMERA PASSWORD</label>
            <input type="password" v-model="newCamera.password" placeholder="Enter CAMERA PASSWORD..." />
          </div>
        </div>

        <button class="add-btn" @click="addCamera">
          <span class="plus">+</span> Add CAMERA
        </button>
      </div>

      <div v-if="cameras.length > 0" class="linked-section">
        <h4 class="section-title">LINKED CAMERAS ({{ cameras.length }})</h4>
        
        <div class="camera-list">
          <div 
            v-for="camera in cameras" 
            :key="camera.id" 
            :class="['camera-item', { active: selectedCameraName === camera.name }]"
            @click="selectCamera(camera.name)"
          >
            <div class="camera-info">
              <div class="camera-name">
                {{ camera.name }} 
                <span v-if="camera.slot !== null" style="font-size: 12px; color: #707eae; font-weight: 500;">
                  (Slot {{ camera.slot + 1 }})
                </span>
              </div>
              <div class="camera-meta">
                <span class="camera-url">{{ camera.url }}</span>
              </div>
            </div>
            <div class="status">
              <span class="status-dot"></span> Active
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useCameraStore } from '../../stores/cameraStore';

interface CameraForm {
  name: string;
  url: string;
  username: string;
  password: string;
}

const cameraStore = useCameraStore();

const newCamera = ref<CameraForm>({
  name: '',
  url: '',
  username: '',
  password: '',
});

const topMessage = ref<string | null>(null);

// 코파일럿의 복잡한 찌꺼기를 지우고 store의 반응형 배열을 다이렉트로 연결
const cameras = computed(() => cameraStore.cameras);
const selectedCameraName = ref<string | null>('');

const addCamera = async () => {
  if (!newCamera.value.name.trim() || !newCamera.value.url.trim()) {
    alert('카메라 연결에 필요한 정보를 모두 입력해주세요.');
    return;
  }
  
  // 중복 URL 체크
  // 중복 URL 체크
  if (cameras.value.some(c => c.url === newCamera.value.url.trim())) {
    topMessage.value = '이미 등록된 CAMERA URL입니다.';
    setTimeout(() => { topMessage.value = null; }, 5000);
    return;
  }

  try {
    // REST API를 쓰지 않고 개편된 스토어의 순수 웹소켓 액션 호출
    const created = await cameraStore.addCamera({
      name: newCamera.value.name.trim(),
      url: newCamera.value.url.trim(),
      username: newCamera.value.username.trim() || undefined,
      password: newCamera.value.password || undefined,
    });

    // 첫 카메라 등록 시 자동 선택 효과
    if (cameras.value.length === 1) {
      selectedCameraName.value = created.name;
    }

    // 폼 초기화
    newCamera.value = { name: '', url: '', username: '', password: '' };
  } catch (e) {
    console.error(e);
    const message = e instanceof Error ? e.message : '카메라 등록 중 알 수 없는 오류가 발생했습니다.';
    topMessage.value = `카메라 등록 실패: ${message}`;
    // 5초 후 자동으로 사라지게 함
    setTimeout(() => { topMessage.value = null; }, 5000);
  }
};

const selectCamera = (name: string) => {
  selectedCameraName.value = name;
};
</script>

<style scoped>
/* 질문자님의 기존 고유 가이드라인 디자인 스펙을 100% 보존하기 위해
  기존 원본 CSS 스타일 코드를 그대로 유지합니다.
*/
.camera-management {
  width: 100%;
  height: 100%;            
  background-color: #ffffff;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
  box-sizing: border-box;
  font-family: 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;  
}

.top-popup {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  background: rgba(27,37,89,0.95);
  color: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(13,27,34,0.2);
  font-weight: 700;
  font-size: 13px;
}

.header-zone {
  display: flex;
  justify-content: space-between; 
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
}

.title {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #1b2559;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.sparkle-icon {
  color: #1b2559;
  font-size: 16px;
}

.linked-info {
  font-size: 13px;
  color: #a3aed0;
  font-weight: 600;
  white-space: nowrap;
}

.linked-info .highlight {
  color: #1b2559;
  font-weight: 700;
}

.body-zone {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.form-container {
  background: #ffffff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  width: 100%;
  box-sizing: border-box;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}

.name-group {
  grid-column: span 2;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 11px;
  font-weight: 700;
  color: #a3aed0;
  letter-spacing: 0.3px;
}

.form-group input {
  height: 38px;            
  border: 1px solid #e0e5f2;
  border-radius: 12px;
  padding: 0 12px;
  font-size: 13px;
  color: #2b3674;
  background-color: #ffffff;
  outline: none;
  box-sizing: border-box;
  width: 100%;
}

.form-group input:focus {
  border-color: #707eae;
}

.add-btn {
  width: 100%;
  height: 40px;            
  background-color: #f4f7fe;
  color: #707eae;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  border-radius: 10px;
  border: 1px solid rgba(13, 27, 34, 0.2); 
}

.add-btn:hover {
  background-color: #e2e8f0;
  color: #1a3ba5;
}

.linked-section {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 12px;
  font-weight: 700;
  color: #a3aed0;
  margin: 0 0 10px 4px;
  letter-spacing: 0.5px;
}

.camera-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: visible;  
  width: 100%;
  max-width: 550px;   
  margin: 0 auto;     
}

.camera-item {
  background: #ffffff;
  border: 1px solid #e9edf7;
  border-radius: 14px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;        
  box-sizing: border-box; 
}

.camera-item:hover {
  background-color: #f8faff;
  border-color: #d1d9e8;
}

.camera-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

.camera-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.camera-name {
  font-size: 15px;
  font-weight: 700;
  color: #2b3674;
}

.camera-item.active .camera-name {
  color: #1a3ba5;
}

.camera-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #a3aed0;
  font-weight: 500;
}

.status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #a3aed0;
  font-weight: 600;
}

.status-dot {
  width: 7px;
  height: 7px;
  background-color: #01ca51;
  border-radius: 50%;
}
</style>