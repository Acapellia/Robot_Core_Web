<template>
  <div class="hub-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        HUB MANAGEMENT
      </h3>
      <!-- 💡 변경: 고정된 이름 대신 selectedHubId(선택된 IP)가 실시간으로 보이도록 수정 -->
      <span class="linked-info">
        Linked to: <span class="highlight">{{ selectedHubId || 'None' }}</span>
      </span>
    </div>

    <div class="body-zone">
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group">
            <label>HUB IP</label>
            <input type="text" v-model="newHub.ip" placeholder="Enter HUB IP..." />
          </div>
          <div class="form-group">
            <label>HUB PORT</label>
            <input type="text" v-model="newHub.port" placeholder="Enter HUB PORT..." />
          </div>
        </div>

        <button class="add-btn" @click="addHub">
          <span class="plus">+</span> Add HUB
        </button>
      </div>

      <div v-if="hubs.length > 0" class="linked-section">
        <h4 class="section-title">LINKED HUBS ({{ hubs.length }})</h4>
        
        <div class="hub-list">
          <div 
            v-for="hub in hubs" 
            :key="hub.ip" 
            :class="['hub-item', { active: selectedHubId === hub.ip }]"
            @click="selectHub(hub.ip)"
          >
            <div class="hub-info">
              <div class="hub-ip">{{ hub.ip }}</div>
              <div class="hub-port">{{ hub.port }}</div>
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
import { storeToRefs } from 'pinia';
import { useHubStore } from '../../stores/hubStore';

const hubStore = useHubStore();
const { hubs, selectedHubId, wsConnected, errorMsg } = storeToRefs(hubStore);
const { connectHub, selectHub } = hubStore;

const newHub = ref({ ip: '', port: '' });

const addHub = () => {
  if (!newHub.value.ip.trim() || !newHub.value.port.trim()) {
    alert('HUB IP와 PORT를 입력해주세요.');
    return;
  }
  if (hubs.value.some(h => h.ip === newHub.value.ip)) {
    alert('이미 등록된 HUB IP입니다.');
    return;
  }
  if (!wsConnected.value) {
    alert('브로드캐스트 매니저와의 연결이 끊어졌습니다. 새로고침 해주세요.');
    return;
  }
  connectHub(newHub.value.ip, newHub.value.port);
  newHub.value = { ip: '', port: '' };
};
</script>

<style scoped>
/* 메인 카드 스타일 */
.hub-management {
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

/* 연결된 허브 리스트 섹션 */
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
.hub-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: visible;  
  
  width: 100%;
  max-width: 550px;   /* 💡 추가: 아이템들이 늘어날 수 있는 최대 가로 크기를 제한 */
  margin: 0 auto;     /* 💡 추가: 가로 크기가 줄어든 리스트를 화면 가운데로 정렬 */
}

/* 개별 허브 아이템 기본 상태 */
.hub-item {
  background: #ffffff;
  border: 1px solid #e9edf7;
  border-radius: 14px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  width: 100%;        /* 💡 부모인 .hub-list가 지정한 max-width(550px)에 가로 꽉 차게 맞춤 */
  box-sizing: border-box; /* 패딩 때문에 가로가 터지는 것 방지 */
}

.hub-item:hover {
  background-color: #f8faff;
  border-color: #d1d9e8;
}

/* 선택 효과 */
.hub-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

.hub-ip {
  font-size: 15px;
  font-weight: 700;
  color: #2b3674;
}

/* 선택 시 텍스트 색상 변경 */
.hub-item.active .hub-ip {
  color: #1a3ba5;
}

.hub-port {
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