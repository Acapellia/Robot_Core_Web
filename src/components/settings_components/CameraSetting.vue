<template>
  <div class="camera-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        CAMERA MANAGEMENT
      </h3>
      <!-- 💡 변경: selectedCameraName(선택된 카메라 이름)이 실시간으로 보이도록 수정 -->
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
          <div class="form-group">
            <label>CAMERA IP</label>
            <input type="text" v-model="newCamera.ip" placeholder="Enter CAMERA IP..." />
          </div>
          <div class="form-group">
            <label>CAMERA PORT</label>
            <input type="text" v-model="newCamera.port" placeholder="Enter CAMERA PORT..." />
          </div>
          <div class="form-group">
            <label>CAMERA ID</label>
            <input type="text" v-model="newCamera.id" placeholder="Enter CAMERA ID..." />
          </div>
          <div class="form-group">
            <label>CAMERA PASSWORD</label>
            <input type="password" v-model="newCamera.pw" placeholder="Enter CAMERA PASSWORD..." />
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
            :key="camera.ip" 
            :class="['camera-item', { active: selectedCameraId === camera.ip }]"
            @click="selectCamera(camera.ip)"
          >
            <!-- 💡 변경: 윗줄에 카메라 이름, 아랫줄에 IP와 PORT 배치 -->
            <div class="camera-info">
              <div class="camera-name">{{ camera.name }}</div>
              <div class="camera-meta">
                <span class="camera-ip">{{ camera.ip }}</span>
                <span class="divider">:</span>
                <span class="camera-port">{{ camera.port }}</span>
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

interface Camera {
  name: string;
  ip: string;
  port: string;
  id: string;
  pw: string;
}

const newCamera = ref<Camera>({
  name: '',
  ip: '',
  port: '',
  id: '',
  pw: '',
});

const cameras = ref<Camera[]>([]);
const selectedCameraId = ref<string | null>('');

// 💡 추가: 현재 선택된 카메라 ID(IP)를 기반으로 카메라 이름을 실시간으로 찾아 반환하는 computed 속성
const selectedCameraName = computed(() => {
  const found = cameras.value.find(c => c.ip === selectedCameraId.value);
  return found ? found.name : 'None';
});

const addCamera = () => {
  if (!newCamera.value.name.trim() || !newCamera.value.ip.trim() || !newCamera.value.port.trim()) {
    alert('카메라 연결에 필요한 정보를 모두 입력해주세요.');
    return;
  }
  
  if (cameras.value.some(c => c.ip === newCamera.value.ip)) {
    alert('이미 등록된 CAMERA IP입니다.');
    return;
  }

  cameras.value.push({ ...newCamera.value });
  
  if (cameras.value.length === 1) {
    selectedCameraId.value = newCamera.value.ip;
  }

  newCamera.value = { name: '', ip: '', port: '', id: '', pw: '' };
};

const selectCamera = (id: string) => {
  selectedCameraId.value = id;
};
</script>

<style scoped>
/* 메인 카드 스타일 */
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

/* 헤더 영역 */
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

/* 바디 영역 */
.body-zone {
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 흰색 폼 박스 */
.form-container {
  background: #ffffff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  width: 100%;
  box-sizing: border-box;
}

/* 그리드 레이아웃 */
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

/* 추가 버튼 */
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

/* 연결된 카메라 리스트 섹션 */
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

/* 내부 스크롤바 완전 제거 및 유연 확장 허용 */
.camera-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: visible;  
  width: 100%;
  max-width: 550px;   
  margin: 0 auto;     
}

/* 개별 카메라 아이템 기본 상태 */
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

/* 선택 효과 */
.camera-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

/* 💡 추가/변경: 내부 리스트 레이아웃 스타일링 */
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

/* 선택 시 카메라 이름 텍스트 색상 강조 */
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

.divider {
  color: #cbd5e1;
}

/* 상태 표시 */
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