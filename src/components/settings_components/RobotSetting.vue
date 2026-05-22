<template>
  <div class="robot-management card">
    <div class="header-zone">
      <h3 class="title">
        <span class="sparkle-icon">✦</span>
        ROBOT MANAGEMENT
      </h3>
      <!-- 💡 변경: selectedRobotName(선택된 로봇 이름)이 실시간으로 보이도록 수정 -->
      <span class="linked-info">
        Linked to: <span class="highlight">{{ selectedRobotName || 'None' }}</span>
      </span>
    </div>

    <div class="body-zone">
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group name-group">
            <label>ROBOT NAME</label>
            <input type="text" v-model="newRobot.name" placeholder="Enter name..." />
          </div>
          <div class="form-group">
            <label>ROBOT IP</label>
            <input type="text" v-model="newRobot.ip" placeholder="Enter ROBOT IP..." />
          </div>
          <div class="form-group">
            <label>ROBOT PORT</label>
            <input type="text" v-model="newRobot.port" placeholder="Enter ROBOT PORT..." />
          </div>
        </div>

        <button class="add-btn" @click="addRobot">
          <span class="plus">+</span> Add ROBOT
        </button>
      </div>

      <div v-if="robots.length > 0" class="linked-section">
        <h4 class="section-title">LINKED ROBOTS ({{ robots.length }})</h4>
        
        <div class="robot-list">
          <div 
            v-for="robot in robots" 
            :key="robot.ip" 
            :class="['robot-item', { active: selectedRobotId === robot.ip }]"
            @click="selectRobot(robot.ip)"
          >
            <!-- 💡 변경: 윗줄에 로봇 이름, 아랫줄에 IP와 PORT 배치 -->
            <div class="robot-info">
              <div class="robot-name">{{ robot.name }}</div>
              <div class="robot-meta">
                <span class="robot-ip">{{ robot.ip }}</span>
                <span class="divider">:</span>
                <span class="robot-port">{{ robot.port }}</span>
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

interface Robot {
  name: string;
  ip: string;
  port: string;
}

const newRobot = ref<Robot>({
  name: '',
  ip: '',
  port: '',
});

const robots = ref<Robot[]>([]);
const selectedRobotId = ref<string | null>('');

// 💡 추가: 현재 선택된 로봇 ID(IP)를 기반으로 로봇 이름을 실시간으로 찾아 반환하는 computed 속성
const selectedRobotName = computed(() => {
  const found = robots.value.find(r => r.ip === selectedRobotId.value);
  return found ? found.name : 'None';
});

const addRobot = () => {
  if (!newRobot.value.name.trim() || !newRobot.value.ip.trim() || !newRobot.value.port.trim()) {
    alert('로봇 연결에 필요한 정보를 모두 입력해주세요.');
    return;
  }
  
  if (robots.value.some(r => r.ip === newRobot.value.ip)) {
    alert('이미 등록된 ROBOT IP입니다.');
    return;
  }

  robots.value.push({ ...newRobot.value });
  
  if (robots.value.length === 1) {
    selectedRobotId.value = newRobot.value.ip;
  }

  newRobot.value = { name: '', ip: '', port: '' };
};

const selectRobot = (id: string) => {
  selectedRobotId.value = id;
};
</script>

<style scoped>
/* 메인 카드 스타일 */
.robot-management {
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

/* 연결된 로봇 리스트 섹션 */
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
.robot-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: visible;  
  width: 100%;
  max-width: 550px;   
  margin: 0 auto;     
}

/* 개별 로봇 아이템 기본 상태 */
.robot-item {
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

.robot-item:hover {
  background-color: #f8faff;
  border-color: #d1d9e8;
}

/* 선택 효과 */
.robot-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

/* 💡 추가/변경: 내부 리스트 레이아웃 스타일링 */
.robot-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.robot-name {
  font-size: 15px;
  font-weight: 700;
  color: #2b3674;
}

/* 선택 시 로봇 이름 텍스트 색상 강조 */
.robot-item.active .robot-name {
  color: #1a3ba5;
}

.robot-meta {
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