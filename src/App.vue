<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import NewspaperRack from './components/NewspaperRack.vue';
import MemoryTable from './components/MemoryTable.vue';
import Gramophone from './components/Gramophone.vue';
import BackgroundCanvas from './components/BackgroundCanvas.vue';

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

const handlePaperSelect = (payload) => {
  activePaper.value = payload.paper;
  transitionRect.value = payload.rect;
  resetIdleTimer();
};

onMounted(() => {
  window.addEventListener('mousemove', resetIdleTimer);
  window.addEventListener('click', resetIdleTimer);
  window.addEventListener('touchstart', resetIdleTimer);
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
