<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import NewspaperRack from './components/NewspaperRack.vue';
import MemoryTable from './components/MemoryTable.vue';
import Gramophone from './components/Gramophone.vue';
import BackgroundCanvas from './components/BackgroundCanvas.vue';
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

const activePaper = ref(null);
const transitionRect = ref(null);
const isIdle = ref(true);

let idleTimeout = null;
const IDLE_LIMIT = 180000; // 3 minutes

const resetIdleTimer = () => {
  if (idleTimeout) clearTimeout(idleTimeout);
  isIdle.value = false;
  if (activePaper.value) {
    idleTimeout = setTimeout(() => {
      activePaper.value = null; // Auto retract
      isIdle.value = true;
    }, IDLE_LIMIT);
  }
};

const startTour = () => {
  const driverObj = driver({
    showProgress: true,
    overlayOpacity: 0.85,
    nextBtnText: '下一步',
    prevBtnText: '上一步',
    doneBtnText: '知道了',
    steps: [
      { 
        element: '#newspaper-rack-trigger', 
        popover: { 
          title: '時光報架', 
          description: '點擊此處可翻閱 1913 年的《臺灣日日新報》，探索當年的新聞軼事。', 
          side: "right", 
          align: 'start' 
        } 
      },
      { 
        element: '#gramophone-trigger', 
        popover: { 
          title: '復古留聲機', 
          description: '點擊留聲機可開啟語音導覽，為您朗讀報紙內容，沉浸在歷史氛圍中。', 
          side: "left", 
          align: 'start' 
        } 
      },
    ]
  });

  driverObj.drive();
};

const handlePaperSelect = (payload) => {
  activePaper.value = payload.paper;
  transitionRect.value = payload.rect;
  resetIdleTimer();
};

onMounted(() => {
  window.addEventListener('mousemove', resetIdleTimer);
  window.addEventListener('click', resetIdleTimer);
  window.addEventListener('touchstart', resetIdleTimer);
  
  // 延遲啟動導覽
  setTimeout(() => {
    startTour();
  }, 1500);
});

onUnmounted(() => {
  window.removeEventListener('mousemove', resetIdleTimer);
  window.removeEventListener('click', resetIdleTimer);
  window.removeEventListener('touchstart', resetIdleTimer);
  if (idleTimeout) clearTimeout(idleTimeout);
});

watch(activePaper, (newVal) => {
  resetIdleTimer();
});
</script>

<template>
  <div class="scene-container">
    <BackgroundCanvas />
    <div class="scene-wrapper">
      <NewspaperRack 
        @select-paper="handlePaperSelect" 
        :current-active="activePaper"
      />
      
      <!-- 移除舊版 MemoryTable，統一使用 NewspaperRack 的擬真飛行動畫 -->
      
      <Gramophone :active-paper-content="activePaper ? (activePaper.content || activePaper.title) : null" />

      <!-- Guide Removed -->
    </div>
  </div>
</template>

<style scoped lang="scss">
/* Styles moved to global SCSS for cleaner component */
</style>
