<template>
  <div class="settings-container" :style="{padding: '0px'}">
    <div class="full-width-flex">
      <!-- LEFT -->
      <div class="settings-left" v-if="contents.left.enabled" :style="{flex: `${contents.left.ratio} 1 0%` }">
        <div class="left-container" :style="leftContainerStyle">
          <div class="robot-core-setting" :style="robotCoreSettingStyle">
            <component
              :is="contents.left.robot_core_setting.component"
              v-bind="contents.left.robot_core_setting.props"
            />
          </div>
          <div class="robot-setting" :style="robotSettingStyle">
            <component
              :is="contents.left.robot_setting.component"
              v-bind="contents.left.robot_setting.props"
            />
          </div>
          <div class="camera-setting" :style="cameraSettingStyle">
            <component
              :is="contents.left.camera_setting.component"
              v-bind="contents.left.camera_setting.props"
            />
          </div>
        </div>
      </div>
      <!-- RIGHT -->
      <div class="settings-right" v-if="contents.right.enabled" :style="{flex: `${contents.right.ratio} 1 0%` }">
        <div class="right-container" :style="rightContainerStyle">
          <div class="robot-patrol-setting" :style="robotPatrolSettingStyle">
            <component
              :is="contents.right.robot_patrol_setting.component"
              v-bind="contents.right.robot_patrol_setting.props"
            />
          </div>
          <div class="robot-event-setting" :style="robotEventSettingStyle">
            <component
              :is="contents.right.robot_event_setting.component"
              v-bind="contents.right.robot_event_setting.props"
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
    // 세로 3 영역: Robot Core, Robot, Camera 세팅
    robot_core_setting: { component: markRaw(RobotCoreSetting), props: {} },
    robot_setting: { component: markRaw(RobotSetting), props: {} },
    camera_setting: { component: markRaw(CameraSetting), props: {} },
    // 비율 (0~1)
    topRatio: 0.33,
    middleRatio: 0.33,
    // gap between vertical areas
    gap: '15px',
  },
  right: {
    enabled: true,
    ratio: 0.75,
    // 세로 2 영역: Robot Patrol, Robot Event 세팅
    robot_patrol_setting: { component: markRaw(RobotPatrolSetting), props: {} },
    robot_event_setting: { component: markRaw(RobotEventSetting), props: {} },
    // 가운데를 분할하는 비율 ( 0~1 )
    middleRatio: 0.6,
    // gap between vertical areas
    gap: '15px',
  },
})

const robotCoreSettingStyle = computed<CSSProperties>(() => ({ flex: `${contents.left.topRatio} 1 0%`, minHeight: '0' }))
const robotSettingStyle = computed<CSSProperties>(() => ({ flex: `${contents.left.middleRatio} 1 0%`, minHeight: '0' }))
const cameraSettingStyle = computed<CSSProperties>(() => ({ flex: `${1 - contents.left.topRatio - contents.left.middleRatio} 1 0%`, minHeight: '0' }))

const robotPatrolSettingStyle = computed<CSSProperties>(() => ({ flex: `${contents.right.middleRatio} 1 0%`, minHeight: '0' }))
const robotEventSettingStyle = computed<CSSProperties>(() => ({ flex: `${1 - contents.right.middleRatio} 1 0%`, minHeight: '0' }))

const leftContainerStyle = computed<CSSProperties>(() => ({ display: 'flex', flexDirection: 'column', gap: contents.left.gap, minHeight: '0' }))
const rightContainerStyle = computed<CSSProperties>(() => ({ display: 'flex', flexDirection: 'column', gap: contents.right.gap, minHeight: '0' }))
</script>

<style scoped>
.settings-container { height: 100%; }
.full-width-flex {  width: 100%; height: 100%; display: flex; gap: 12px; }

.left-container { height: 100%; min-height: 0; }
.right-container { height: 100%; min-height: 0; }
</style>

