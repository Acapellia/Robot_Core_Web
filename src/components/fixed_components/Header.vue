<template>
  <header class="app-header">
    <div class="title">
      <img :src="logo" alt="logo" class="header-logo" />
      <h1 class="page-title">Robot Control Page</h1>
    </div>

    <div class="user-profile-section">
      <div class="user-meta">
        <span class="user-name">Admin_User</span>
        <span class="live-time">{{ currentTime }}</span>
      </div>

      <div class="user-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import logo from '../../assets/icons/Intellivix_logo.png';
import { useHeader } from '../../composables/useHeader';

const { currentTime } = useHeader();
</script>

<style scoped>
.app-header {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px; /* 대시보드 전체 여백에 맞춰 확장 */
  box-sizing: border-box;
  background-color: #ffffff;
  font-family: 'Segoe UI', Roboto, sans-serif;
}

.app-header .title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.page-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f7f7f7; /* 관제 페이지 메인 딥블루 컬러 */
}

/* 💡 우측 정렬 유저 섹션 컨테이너 */
.user-profile-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* 두 줄 텍스트 배치 구조 */
.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end; /* 오른쪽 정렬 고정 */
  justify-content: center;
  gap: 4px;
}

.user-name {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.2;
}

.live-time {
  font-size: 11px;
  font-weight: 600;
  color: #bac0d1; /* 차분한 그레이시 블루 색상 적용 */
  line-height: 1.2;
  font-family: 'Segoe UI', monospace; /* 숫자 정렬 깨짐 방지 */
}

/* 원형 사용자 아이콘 스타일 */
.user-avatar {
  width: 34px;
  height: 34px;
  background-color: #f4f7fe;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4250ab;
  border: 1px solid #e9edf7;
  padding: 7px;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.user-avatar svg {
  width: 100%;
  height: 100%;
}

.user-profile-section:hover .user-avatar {
  background-color: #e4f2ff;
  color: #1a3ba5;
  border-color: #bfaee3;
}
</style>