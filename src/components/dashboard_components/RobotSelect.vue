<template>
  <div class="robot-select card">
    <div class="header">
      <h3 class="title">
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
        Robot Lists
      </h3>
    </div>

    <div :class="['body', robots.length === 0 ? 'empty' : '']">
      <div v-if="robots.length === 0" class="empty-state">
        연결된 로봇이 없습니다.
      </div>

      <div v-else class="robot-list">
        <div 
          v-for="robot in robots" 
          :key="robot.id"
          :class="['robot-item', { active: selectedRobotId === robot.id }]"
          @click="selectRobot(robot.id)"
        >
          <div class="robot-image-box">
            <img 
              v-if="robot.imageUrl" 
              :src="robot.imageUrl" 
              :alt="robot.id" 
              class="robot-api-img"
            />
            <svg v-else class="default-robot-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM6 10h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2z"/>
              <circle cx="9" cy="15" r="1"/>
              <circle cx="15" cy="15" r="1"/>
            </svg>
          </div>

          <div class="robot-info">
            <div class="robot-name">
              {{ robot.id }} <span v-if="robot.isMain" class="main-badge">(Main)</span>
            </div>
            <div :class="['robot-status', (robot.telemetry?.status || '').toLowerCase()]">
              <span class="status-dot"></span>
              {{ robot.telemetry?.status }}
            </div>
          </div>

          <div class="arrow-box">
            <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotList } from '../../composables/useRobotList';

const { robots, selectedRobotId, selectRobot } = useRobotList();
</script>

<style scoped>
/* 테마 상태별 변수 색상 구성 */
.patrolling { --status-color: #05cd99; }
.idle { --status-color: #ff9f43; }
.offline { --status-color: #a3aed0; }

/* 💡 가로 패딩 내부 컴포넌트 유동 제어를 위한 정밀 설계 */
.robot-select {
  width: 100%;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2); /* 얇은 테두리 추가 */
  font-family: 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

/* 💡 변경 포인트: flex 구조를 재정비하여 완벽한 좌측 정렬(justify-content: flex-start) 구현 */
.header {
  display: flex;
  justify-content: flex-start; 
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
  width: 100%;
}

.title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #a3aed0;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-icon { width: 16px; height: 16px; }

/* 본문 격자 리스트 */
.body {
  flex: 1;
  overflow-y: auto;
  width: 100%;
}

/* body가 비었을 때 중앙 정렬 처리 */
.body.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.robot-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%; /* 부모 격자에 완전히 맞춤 */
}

/* 💡 변경 포인트: width: 100%와 box-sizing을 명시하여 좌우 여백을 가득 채우도록 고정 */
.robot-item {
  display: flex;
  align-items: center;
  width: 100%; 
  padding: 14px 20px;
  box-sizing: border-box;
  background-color: #ffffff;
  border: 1px solid #e9edf7;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.robot-item:hover {
  background-color: #f8faff;
  border-color: #d1d9e8;
}

/* 선택 활성화 인디케이터 */
.robot-item.active {
  background-color: #f3eef9;
  border-color: #bfaee3;
}

/* 💡 변경 포인트: 폴리곤 레이아웃을 걷어내고 정방형 크롭 형태의 이미지 컨테이너 구축 */
.robot-image-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background-color: #f4f7fe;
  border-radius: 10px;
  flex-shrink: 0;
  margin-right: 16px;
  overflow: hidden; /* 영역 밖으로 이미지가 터져 나가는 것 방지 */
  transition: all 0.2s ease;
}

.robot-item.active .robot-image-box {
  background-color: #ffffff;
  box-shadow: 0 4px 10px rgba(163, 112, 226, 0.1);
}

/* API로부터 주입받을 실제 로봇 이미지 채우기 속성 */
.robot-api-img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 비율을 깨뜨리지 않고 가득 채움 */
}

/* 이미지 로드 전 기본 뼈대 대체 아이콘 */
.default-robot-icon {
  width: 20px;
  height: 20px;
  color: #a3aed0;
}
.robot-item.active .default-robot-icon {
  color: #1a3ba5;
}

/* 중앙 메인 텍스트 정보 구역 */
.robot-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.robot-name {
  font-size: 15px;
  font-weight: 700;
  color: #2b3674;
}
.robot-item.active .robot-name {
  color: #1a3ba5;
}
.main-badge {
  font-size: 14px;
  font-weight: 700;
}

.robot-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--status-color);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--status-color);
}

/* 우측 화살표 */
.arrow-box {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.arrow-icon {
  width: 14px;
  height: 14px;
  color: #e9edf7;
  transition: all 0.2s ease;
}
.robot-item:hover .arrow-icon {
  color: #a3aed0;
}
.robot-item.active .arrow-icon {
  color: #bfaee3;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #a3aed0;
  font-size: 14px;
}

/* 가로/세로 내부 스크롤바 제어 */
.body::-webkit-scrollbar { width: 4px; }
.body::-webkit-scrollbar-track { background: transparent; }
.body::-webkit-scrollbar-thumb { background: #e9edf7; border-radius: 4px; }
</style>