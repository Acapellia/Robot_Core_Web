<template>
  <div class="camera-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        CAMERA MANAGEMENT
      </h3>
      <span class="linked-info">Linked to: <span class="highlight">Observ_Alpha</span></span>
    </div>

    <div class="body-zone">
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group">
            <label>CAMERA NAME</label>
            <input type="text" v-model="newCamera.name" placeholder="Enter name..." />
          </div>
          <div class="form-group">
            <label>IP ADDRESS</label>
            <input type="text" v-model="newCamera.ip" placeholder="Enter IP address..." />
          </div>
          <div class="form-group">
            <label>ID</label>
            <input type="text" v-model="newCamera.id" placeholder="Enter ID..." />
          </div>
          <div class="form-group">
            <label>PASSWORD</label>
            <input type="password" v-model="newCamera.password" placeholder="••••" />
          </div>
        </div>

        <button class="add-btn" @click="addCamera">
          <span class="plus">+</span> Add Camera
        </button>
      </div>

      <div v-if="cameras.length > 0" class="linked-section">
        <h4 class="section-title">LINKED CAMERAS ({{ cameras.length }})</h4>
        
        <div class="camera-list">
          <div 
            v-for="(camera, index) in cameras" 
            :key="index" 
            class="camera-item"
            :class="{ 'first-item': index === 0 }"
          >
            <div class="camera-info">
              <div class="camera-name">{{ camera.name }}</div>
              <div class="camera-ip">{{ camera.ip }}</div>
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
import { ref } from 'vue';

interface Camera {
  name: string;
  ip: string;
  id: string;
  password?: string;
}

const newCamera = ref<Camera>({
  name: '',
  ip: '',
  id: '',
  password: ''
});

const cameras = ref<Camera[]>([]);

const addCamera = () => {
  if (!newCamera.value.name.trim() || !newCamera.value.ip.trim()) {
    alert('Camera Name과 IP Address를 입력해주세요.');
    return;
  }
  cameras.value.push({ ...newCamera.value });
  newCamera.value = { name: '', ip: '', id: '', password: '' };
};
</script>

<style scoped>
/* 메인 카드 스타일: 초기에는 부모가 할당한 균등 비율(33%)을 꽉 채우되, 콘텐츠 가려짐 없이 자연스레 연동 확장 */
.camera-management {
  width: 100%;
  height: 100%;            
  background-color: #ffffff;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid #e2dbf7;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  
  display: flex;
  flex-direction: column;  
}

/* 헤더 영역 */
.header-zone {
  display: flex;
  justify-content: space-between; 
  align-items: center;
  margin-bottom: 16px;
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
  color: #b05be6;
  font-size: 16px;
}

.linked-info {
  font-size: 13px;
  color: #a3aed0;
  font-weight: 600;
  white-space: nowrap;
}

.linked-info .highlight {
  color: #b05be6;
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

/* 2x2 그리드 레이아웃 */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
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
  /* border-color: #b05be6; */
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
  gap: 10px;
  overflow: visible;        
}

/* 개별 카메라 아이템 */
.camera-item {
  background: #ffffff;
  border-radius: 14px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.camera-item.first-item {
  border-left: 4px solid #a155cf;
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
}

.camera-name {
  font-size: 13px;
  font-weight: 700;
  color: #1b2559;
}

.camera-ip {
  font-size: 11px;
  color: #a3aed0;
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