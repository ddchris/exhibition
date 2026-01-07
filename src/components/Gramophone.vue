<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import gsap from 'gsap';

const props = defineProps(['activePaperContent']);

const isPlaying = ref(false);
const isHovered = ref(false);
const currentText = ref('');
const displayedText = ref('');
let typewriterInterval = null;

// 留聲機原始座標 (1024x1024 基準)
const rawCoords = [
  [899, 267], [837, 282], [815, 296], [773, 336], [746, 398], [749, 443], 
  [756, 464], [797, 496], [832, 499], [877, 492], [921, 462], [945, 477], 
  [945, 505], [941, 509], [916, 515], [908, 506], [896, 504], [886, 514], 
  [884, 535], [841, 536], [784, 547], [792, 559], [791, 597], [773, 613], 
  [813, 671], [821, 676], [882, 673], [896, 666], [899, 653], [1002, 651], 
  [996, 642], [996, 613], [1001, 596], [1018, 587], [960, 549], [971, 517], 
  [970, 467], [948, 436], [976, 371], [973, 332], [960, 299], [951, 289]
];

const dynamicPath = ref('');
const mouseX = ref(0);
const mouseY = ref(0);

const calculateDynamicPath = () => {
  const vW = window.innerWidth;
  const vH = window.innerHeight;
  const sourceDim = 1024;

  // 模擬 object-fit: cover 的縮放邏輯
  const scale = Math.max(vW / sourceDim, vH / sourceDim);
  const offsetX = (vW - sourceDim * scale) / 2;
  const offsetY = (vH - sourceDim * scale) / 2;

  const points = rawCoords.map(([x, y]) => {
    const nx = x * scale + offsetX;
    const ny = y * scale + offsetY;
    return `${nx.toFixed(1)},${ny.toFixed(1)}`;
  });

  dynamicPath.value = `M ${points.join(' L ')} Z`;
};

const handleMouseMove = (e) => {
  if (isHovered.value) {
    mouseX.value = e.clientX;
    mouseY.value = e.clientY;
  }
};

onMounted(() => {
  calculateDynamicPath();
  window.addEventListener('resize', calculateDynamicPath);
  window.addEventListener('mousemove', handleMouseMove);
});

onUnmounted(() => {
  window.removeEventListener('resize', calculateDynamicPath);
  window.removeEventListener('mousemove', handleMouseMove);
  stopPlay();
});

const togglePlay = () => {
  if (isPlaying.value) {
    stopPlay();
    return;
  }
  const textToRead = props.activePaperContent 
    || "大正二年，孫中山先生抵達基隆港，受到民眾熱烈歡迎。市街改正計畫隨之展開，臺北城風貌煥然一新。";
  currentText.value = textToRead;
  isPlaying.value = true;
  startSpeech(textToRead);
};

const startSpeech = (text) => {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  displayedText.value = '';
  if (typewriterInterval) clearInterval(typewriterInterval);
  let charIndex = 0;
  typewriterInterval = setInterval(() => {
    if (charIndex < text.length) {
      displayedText.value += text[charIndex];
      charIndex++;
    } else {
      clearInterval(typewriterInterval);
    }
  }, 250);
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'zh-TW';
  utterance.rate = 0.8; 
  utterance.pitch = 0.9; 
  utterance.onend = () => stopPlay();
  window.speechSynthesis.speak(utterance);
};

const stopPlay = () => {
  isPlaying.value = false;
  currentText.value = '';
  displayedText.value = '';
  if (typewriterInterval) clearInterval(typewriterInterval);
  if (window.speechSynthesis) window.speechSynthesis.cancel();
};
</script>

<template>
  <div class="gramophone-overlay">
    <!-- 注意：這裡不再使用 viewBox，而是直接匹配視窗大小 -->
    <svg class="dynamic-svg-layer">
      <g 
        id="gramophone-trigger"
        class="interactive-group"
        @mouseenter="isHovered = true"
        @mouseleave="isHovered = false"
        @click="togglePlay"
      >
        <path 
          :d="dynamicPath" 
          class="gramophone-path"
          :class="{ 'is-active': isHovered && !isPlaying }"
        />
      </g>
    </svg>

    <div v-if="isHovered && !isPlaying" class="cursor-tooltip" :style="{ top: mouseY + 15 + 'px', left: mouseX + 15 + 'px' }">
      <span class="icon">🔊</span> 開始語音導覽
    </div>

    <div v-if="isPlaying" class="lyrics-container" @click="stopPlay">
      <div class="lyrics-box">
        <div class="playing-status"><span class="pulse-icon">🔊</span> 語音導覽中...</div>
        <div class="lyrics-text">{{ displayedText }}<span class="typewriter-cursor">|</span></div>
        <div class="tap-hint">點擊任意處停止播放</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gramophone-overlay {
  position: fixed;
  inset: 0;
  pointer-events: none; 
  z-index: 30;
}
.dynamic-svg-layer {
  width: 100vw;
  height: 100vh;
  display: block;
}
.interactive-group {
  cursor: pointer;
  pointer-events: auto; 
}
.gramophone-path {
  fill: transparent;
  stroke: transparent;
  stroke-width: 2.5;
  transition: all 0.3s ease;
}
.gramophone-path.is-active {
  fill: rgba(255, 215, 0, 0.15); 
  stroke: #FFD700; 
  stroke-width: 4;
  stroke-dasharray: none;
  animation: none;
}

@keyframes pulsePathGramo {
  0%, 100% { stroke: rgba(255, 215, 0, 0.2); stroke-width: 2; }
  50% { stroke: rgba(255, 215, 0, 1); stroke-width: 3.5; }
}
.cursor-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: #FFD700;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  pointer-events: none;
  white-space: nowrap;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 215, 0, 0.3);
  z-index: 100;
}
.lyrics-container {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  z-index: 200;
  backdrop-filter: blur(2px);
}
.lyrics-box {
  background: rgba(0, 0, 0, 0.75);
  padding: 40px;
  border-radius: 12px;
  max-width: 800px;
  width: 90%;
  text-align: center;
  color: #fff;
}
.lyrics-text {
  font-size: 1.8rem;
  line-height: 1.6;
  font-family: '楷體', 'BiauKai', serif;
}
.typewriter-cursor { animation: blink 1s step-end infinite; color: #FFD700; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.2); } }
.pulse-icon { display: inline-block; animation: pulse 1.5s infinite; }
</style>
