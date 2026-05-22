<template>
  <div class="settings-container" :style="{padding: '0px'}">
    <div class="full-width-flex">
      <div class="settings-left" v-if="contents.left.enabled" :style="{flex: `${contents.left.ratio} 1 0%` }">
        <div class="left-container" :style="leftContainerStyle">
          <div class="robot-core-setting" :style="robotCoreSettingStyle">
            <component
              :is="contents.left.robot_core_setting.component"
              v-bind="contents.left.robot_core_setting.props"
              class="child-component"
            />
          </div>
          <div class="robot-setting" :style="robotSettingStyle">
            <component
              :is="contents.left.robot_setting.component"
              v-bind="contents.left.robot_setting.props"
              class="child-component"
            />
          </div>
          <div class="camera-setting" :style="cameraSettingStyle">
            <component
              :is="contents.left.camera_setting.component"
              v-bind="contents.left.camera_setting.props"
              class="child-component"
            />
          </div>
        </div>
      </div>
      <div class="settings-right" v-if="contents.right.enabled" :style="{flex: `${contents.right.ratio} 1 0%` }">
        <div class="right-container" :style="rightContainerStyle">
          <div class="robot-patrol-setting" :style="robotPatrolSettingStyle">
            <component
              :is="contents.right.robot_patrol_setting.component"
              v-bind="contents.right.robot_patrol_setting.props"
              class="child-component"
            />
          </div>
          <div class="robot-event-setting" :style="robotEventSettingStyle">
            <component
              :is="contents.right.robot_event_setting.component"
              v-bind="contents.right.robot_event_setting.props"
              class="child-component"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, markRaw } from 'vue'
import type { CSSProperties } from 'vue'

// 대쉬보드 좌측 컴포넌트
import RobotCoreSetting from '../components/settings_components/RobotCoreSetting.vue'
import RobotSetting from '../components/settings_components/RobotSetting.vue'
import CameraSetting from '../components/settings_components/CameraSetting.vue'
// 대쉬보드 우측 컴포넌트
import RobotPatrolSetting from '../components/settings_components/RobotPatrolSetting.vue'
import RobotEventSetting from '../components/settings_components/RobotEventSetting.vue'

const contents = reactive({
  left: {
    enabled: true,
    ratio: 0.25,
    robot_core_setting: { component: markRaw(RobotCoreSetting), props: {} },
    robot_setting: { component: markRaw(RobotSetting), props: {} },
    camera_setting: { component: markRaw(CameraSetting), props: {} },
    topRatio: 0.33,
    middleRatio: 0.33,
    gap: '15px',
  },
  right: {
    enabled: true,
    ratio: 0.75,
    robot_patrol_setting: { component: markRaw(RobotPatrolSetting), props: {} },
    robot_event_setting: { component: markRaw(RobotEventSetting), props: {} },
    middleRatio: 0.6,
    gap: '15px',
  },
})

// ★ 핵심 보정: 감싸는 수직 박스에 display: flex를 명시해 주어야 
// 내부에 바인딩되는 실제 컴포넌트 카드들이 찌그러지지 않고 부모 높이를 100% 꽉 채울 수 있습니다.
const robotCoreSettingStyle = computed<CSSProperties>(() => ({ flex: `${contents.left.topRatio} 1 0%`,   minHeight: '0',}))

const robotSettingStyle = computed<CSSProperties>(() => ({ flex: `${contents.left.middleRatio} 1 0%`,  minHeight: '0',}))

const cameraSettingStyle = computed<CSSProperties>(() => ({ flex: `${1 - contents.left.topRatio - contents.left.middleRatio} 1 0%`,  minHeight: '0',}))

const robotPatrolSettingStyle = computed<CSSProperties>(() => ({   flex: `${contents.right.middleRatio} 1 0%`,   minHeight: '0',}))

const robotEventSettingStyle = computed<CSSProperties>(() => ({ flex: `${1 - contents.right.middleRatio} 1 0%`,   minHeight: '0',}))

const leftContainerStyle = computed<CSSProperties>(() => ({ display: 'flex', flexDirection: 'column', gap: contents.left.gap, minHeight: '0' }))


const rightContainerStyle = computed<CSSProperties>(() => ({ display: 'flex', flexDirection: 'column', gap: contents.right.gap, minHeight: '0' }))

</script>

<style scoped>
.settings-container { height: 100%; }
.full-width-flex { width: 100%; height: 100%; display: flex; gap: 12px; }

/* 좌측 메인 영역: 스크롤 및 레이아웃 바운더리 고정 */
.settings-left {
  height: 100%;
  overflow-y: auto;         
  padding-right: 6px;       
  box-sizing: border-box;
}

.left-container { 
  width: 100%; 
  
}

.settings-right { 
  height: 100%; 
  overflow-y: auto; /* 우측도 내용물 많아질 경우 대비해 스크롤 세팅 */
  padding-right: 6px;
  box-sizing: border-box;
}
.right-container { 
  width: 100%; 
  height: 100%;
}

/* ★ 주입되는 하위 컴포넌트(들)가 부모 영역의 높이를 무조건 100% 꽉 채우도록 강제 정의 */
.child-component {
  width: 100% !important;
  height: 100% !important;
  flex: 1 1 auto;
}

/* 스크롤바 디자인 */
.settings-left::-webkit-scrollbar,
.settings-right::-webkit-scrollbar {
  width: 6px;
}
.settings-left::-webkit-scrollbar-track,
.settings-right::-webkit-scrollbar-track {
  background: transparent;
}
.settings-left::-webkit-scrollbar-thumb,
.settings-right::-webkit-scrollbar-thumb {
  background: #e0e5f2;
  border-radius: 10px;
}
.settings-left::-webkit-scrollbar-thumb:hover,
.settings-right::-webkit-scrollbar-thumb:hover {
  background: #b05be6;
}
</style>