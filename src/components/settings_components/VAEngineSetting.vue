<template>
  <div class="va-engine-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        VA ENGINE MANAGEMENT
      </h3>
      <!-- 💡 변경: selectedVAEngineIP(선택된 VA 엔진 IP)이 실시간으로 보이도록 수정 -->
      <span class="linked-info">
        Linked to: <span class="highlight">{{ selectedVAEngineIP || 'None' }}</span>
      </span>
    </div>

    <div class="body-zone">
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group">
            <label>VA IP</label>
            <input type="text" v-model="newVAEngine.ip" placeholder="Enter VA IP..." />
          </div>
          <div class="form-group">
            <label>VA PORT</label>
            <input type="text" v-model="newVAEngine.port" placeholder="Enter VA PORT..." />
          </div>
          <div class="form-group">
            <label>VA ID</label>
            <input type="text" v-model="newVAEngine.id" placeholder="Enter VA ID..." />
          </div>
          <div class="form-group">
            <label>VA PASSWORD</label>
            <input type="password" v-model="newVAEngine.pw" placeholder="Enter VA PASSWORD..." />
          </div>
        </div>

        <button class="add-btn" @click="addVAEngine">
          <span class="plus">+</span> Add VA ENGINE
        </button>
      </div>

      <div v-if="vaEngines.length > 0" class="linked-section">
        <h4 class="section-title">LINKED VA ENGINES ({{ vaEngines.length }})</h4>
        
        <div class="va-engine-list">
          <div 
            v-for="vaEngine in vaEngines" 
            :key="vaEngine.ip" 
            :class="['va-engine-item', { active: selectedVAEngineIP === vaEngine.ip }]"
            @click="selectVAEngine(vaEngine.ip)"
          >
            <!-- 💡 변경: 윗줄에 VA 엔진 이름, 아랫줄에 IP와 PORT 배치 -->
            <div class="va-engine-info">
              <div class="va-engine-meta">
                <span class="va-engine-ip">{{ vaEngine.ip }}</span>
                <span class="divider">:</span>
                <span class="va-engine-port">{{ vaEngine.port }}</span>
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
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useVAStore } from '../../stores/vaStore';

const vaStore = useVAStore();
const { vaEngines, selectedVAEngineIP, wsConnected, errorMsg } = storeToRefs(vaStore);
const { connectVA, selectVA } = vaStore;

const newVAEngine = ref({ ip: '', port: '', id: '', pw: '' });

const addVAEngine = () => {
  if (!newVAEngine.value.ip.trim() || !newVAEngine.value.port.trim() || !newVAEngine.value.id.trim() || !newVAEngine.value.pw.trim()) {
    alert('VA 엔진 연결에 필요한 정보를 모두 입력해주세요.');
    return;
  }

  if (vaEngines.value.some((c: any) => c.ip === newVAEngine.value.ip)) {
    alert('이미 등록된 VA 엔진 IP입니다.');
    return;
  }

  if (!wsConnected.value) {
    alert('브로드캐스트 매니저와의 연결이 끊어졌습니다. 새로고침 해주세요.');
    return;
  }

  // 요청 전송
  connectVA(newVAEngine.value.ip, newVAEngine.value.port, newVAEngine.value.id, newVAEngine.value.pw);

  // UI 즉시 반영(백엔드 확인 후 중복 방지를 위해 store가 갱신될 수 있음)
  vaEngines.value.push({ ...newVAEngine.value });
  if (!selectedVAEngineIP.value) selectedVAEngineIP.value = newVAEngine.value.ip;

  newVAEngine.value = { ip: '', port: '', id: '', pw: '' };
};

const selectVAEngine = (ip: string) => {
  selectVA(ip);
};
</script>

<style scoped>
/* 메인 카드 스타일 */
.va-engine-management {
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
.va-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: visible;  
  width: 100%;
  max-width: 550px;   
  margin: 0 auto;     
}

/* 개별 VA 엔진 아이템 기본 상태 */
.va-engine-item {
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

.va-engine-item:hover {
  background-color: #f8faff;
  border-color: #d1d9e8;
}

/* 선택 효과 */
.va-engine-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

/* 💡 추가/변경: 내부 리스트 레이아웃 스타일링 */
.va-engine-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.va-engine-name {
  font-size: 15px;
  font-weight: 700;
  color: #2b3674;
}

/* 선택 시 VA 엔진 이름 텍스트 색상 강조 */
.va-engine-item.active .va-engine-name {
  color: #1a3ba5;
}

.va-engine-meta {
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