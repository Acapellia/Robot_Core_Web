<template>
  <div class="dashboard" :style="dashboardStyle">
    <div class="full-width-flex">
      <div
        class="panel left"
        v-if="contents.left.enabled"
        :style="{ flex: `${contents.left.ratio} 1 0%` }"
      >
        <div class="left-container" :style="leftContainerStyle">
          <div class="left-top" :style="leftTopStyle">
            <component :is="contents.left.top.component" v-bind="contents.left.top.props" />
          </div>
          <div class="left-middle" :style="leftMiddleStyle">
            <component :is="contents.left.middle.component" v-bind="contents.left.middle.props" />
          </div>
          <div class="left-bottom" :style="leftBottomStyle">
            <component :is="contents.left.bottom.component" v-bind="contents.left.bottom.props" />
          </div>
        </div>
      </div>

      <div class="panel center" :style="{ flex: `${contents.center.ratio} 1 0%` }">
        <div class="center-top" :style="centerTopStyle">
          <component :is="contents.center.top.component" v-bind="contents.center.top.props" />
        </div>
        <div class="center-middle" :style="centerMiddleStyle">
          <div class="card">
            <component :is="contents.center.middle.component" v-bind="contents.center.middle.props" />
          </div>
        </div>
        <div class="center-bottom" :style="centerBottomStyle">
          <component :is="contents.center.bottom.component" v-bind="contents.center.bottom.props" />
        </div>
      </div>

      <div
        class="panel right"
        v-if="contents.right.enabled"
        :style="{ flex: `${contents.right.ratio} 1 0%` }"
      >
        <component :is="contents.right.component" v-bind="contents.right.props" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, markRaw } from 'vue'
import RobotController from '../components/RobotController.vue'
import RobotCamGrid from '../components/RobotCamGrid.vue'
import RobotMessage from '../components/RobotMessage.vue'
import RobotInfo from '../components/RobotInfo.vue'
import RobotEvent from '../components/RobotEvent.vue'
import RobotSelect from '../components/RobotSelect.vue'
import RobotMap from '../components/RobotMap.vue'

// 레이아웃 변수: Dashboard에서 제어 (top-grid gaps, center gap)
const layoutVars = reactive({
  topGridRowGap: '10px',
  topGridColGap: '10px',
  centerGap: '10px',
})

const dashboardStyle = computed(() => ({
  '--top-grid-row-gap': layoutVars.topGridRowGap,
  '--top-grid-col-gap': layoutVars.topGridColGap,
  '--center-gap': layoutVars.centerGap,
}))

const Placeholder = {
  props: ['text'],
  template: `<div class="placeholder">{{ text || 'Placeholder' }}</div>`,
}

// 개발자가 이 `contents` 객체를 수정해서 각 영역의 컴포넌트, 크기, 노출 여부를 제어할 수 있습니다.
const contents = reactive({
  left: {
    enabled: true,
    ratio: 0.22,
    // 세로 3 영역: select / info / map
    top: { component: markRaw(RobotSelect), props: {} },
    middle: { component: markRaw(RobotInfo), props: {} },
    bottom: { component: markRaw(RobotMap), props: {} },
    // 비율 (0~1)
    topRatio: 0.35,
    middleRatio: 0.15,
    // gap between left sub-areas (CSS length)
    gap: '15px',
  },
  center: {
    // top / bottom은 실제 컴포넌트(또는 문자열 이름)를 넣어 교체 가능
    top: { component: markRaw(RobotCamGrid), props: {} },
    middle: { component: markRaw(RobotMessage), props: {} },
    bottom: { component: markRaw(RobotController), props: {} },
    // 가운데를 분할하는 비율 (0~1)
    topRatio: 0.45,
    middleRatio: 0.04,
    // 가운데 영역의 전체 비율
    ratio: 0.57,
  },
  right: {
    enabled: true,
    ratio: 0.21,
    component: markRaw(RobotEvent),
    props: {},
  },
})

const centerTopStyle = computed(() => ({ flex: `${contents.center.topRatio} 1 0%`, minHeight: '0' }))
const centerMiddleStyle = computed(() => ({ flex: `${contents.center.middleRatio} 1 0%`, minHeight: '0' }))
const centerBottomStyle = computed(() => ({ flex: `${1 - contents.center.topRatio - contents.center.middleRatio} 1 0%`, minHeight: '0' }))

const leftTopStyle = computed(() => ({ flex: `${contents.left.topRatio} 1 0%`, minHeight: '0' }))
const leftMiddleStyle = computed(() => ({ flex: `${contents.left.middleRatio} 1 0%`, minHeight: '0' }))
const leftBottomStyle = computed(() => ({ flex: `${1 - contents.left.topRatio - contents.left.middleRatio} 1 0%`, minHeight: '0' }))

const leftContainerStyle = computed(() => ({ display: 'flex', flexDirection: 'column', gap: contents.left.gap, minHeight: '0' }))
</script>

<style scoped>
.dashboard { height: 100%; }
.full-width-flex {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 12px;
}
.panel { min-height: 0; overflow: hidden; }
.panel.center { flex: 1 1 auto; display: flex; flex-direction: column; min-width: 0; gap: var(--center-gap); }
.center-top, .center-middle, .center-bottom { overflow: auto; min-height: 0; }
.placeholder { padding: 12px; color: var(--muted-color, #666); }
.center-middle .card { height: 100%; }

/* Left panel sub-areas */
.left-container { height: 100%; min-height: 0; }
.left-top, .left-middle, .left-bottom { overflow: auto; min-height: 0; }
.left-middle .card { height: 100%; }
</style>