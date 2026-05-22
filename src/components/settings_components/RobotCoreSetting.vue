<template>
  <div class="robot-core-setting card">
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
        Robot Hub Setting
      </h3>
    </div>
    <div class="body">
      <p>로봇 허브 설정(RobotCoreSetting)이 표시될 공간입니다.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// 필요한 경우 이곳에 스크립트 로직을 작성합니다.
</script>

<style scoped>
.robot-core-setting {
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  border-radius: 16px;
  border: 1px solid rgba(13, 27, 34, 0.2);
}

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

.body {
  flex: 1;
  overflow-y: auto;
  width: 100%;
}
</style>