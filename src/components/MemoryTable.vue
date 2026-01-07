<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import gsap from 'gsap';

const props = defineProps(['paper', 'fromRect']);
const emit = defineEmits(['reset']);

const tableRef = ref(null);
const paperRef = ref(null);

const mouseX = ref(0);
const mouseY = ref(0);
const showMagnifier = ref(false);

const handleMouseMove = (e) => {
  if (!paperRef.value) return;
  const rect = paperRef.value.getBoundingClientRect();
  mouseX.value = e.clientX - rect.left;
  mouseY.value = e.clientY - rect.top;
  showMagnifier.value = true;
};

const handleMouseLeave = () => {
  showMagnifier.value = false;
};

const maskStyle = computed(() => {
  if (!showMagnifier.value) return { clipPath: 'circle(0% at 0 0)' };
  return { 
    clipPath: `circle(80px at ${mouseX.value}px ${mouseY.value}px)`
  };
});

watch(() => props.paper, async (newVal) => {
  if (newVal) {
    await nextTick();
    if (!paperRef.value) return;
    
    const el = paperRef.value;
    
    // Default animation if no rect provided (fallback)
    let startVars = { opacity: 0, y: -100, scale: 0.8 };
    
    if (props.fromRect) {
      const toRect = el.getBoundingClientRect();
      const deltaX = props.fromRect.left - toRect.left + (props.fromRect.width / 2 - toRect.width / 2);
      const deltaY = props.fromRect.top - toRect.top + (props.fromRect.height / 2 - toRect.height / 2);
      
      startVars = {
        x: deltaX,
        y: deltaY,
        scale: 0.3,
        rotation: -45, // Spin a bit
        opacity: 0,
        z: 200 // Start closer to camera?
      };
    }

    gsap.fromTo(el, 
      startVars,
      { 
        x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, z: 0,
        duration: 1.0, 
        ease: "power2.inOut",
        onStart: () => {
             // Optional: Add shadow burst
        } 
      }
    );
  } else {
    showMagnifier.value = false;
  }
});
</script>

<template>
  <div class="table-container" ref="tableRef">
    <div class="memory-table">
      <div class="table-surface">
        <div v-if="paper" class="active-paper-wrapper" ref="paperRef" 
             @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
          
          <!-- Base Layer: Blurred/Vintage -->
          <div class="newspaper-flat base-layer">
            <div class="newspaper-header">
              <h1>臺灣日日新報</h1>
              <p>{{ paper.year }}年 卷號：第壹陸肆貳號</p>
            </div>
            <div class="newspaper-body">
              <div class="main-column">
                <h2>{{ paper.title }}</h2>
                <p>{{ paper.content }}</p>
                <p class="filler">此處為史料記載之模擬文本內容。當時之社會風貌、政令宣導及各界聞訊皆詳載於此。</p>
              </div>
            </div>
            <button class="close-btn" @click="$emit('reset')">收回報紙</button>
          </div>

          <!-- Top Layer: Sharp/Enhanced (Clipped) -->
          <div class="newspaper-flat sharp-layer" :style="maskStyle">
            <div class="newspaper-header">
              <h1>臺灣日日新報</h1>
              <p>{{ paper.year }}年 卷號：第壹陸肆貳號</p>
            </div>
            <div class="newspaper-body">
              <div class="main-column">
                <h2>{{ paper.title }}</h2>
                <p>{{ paper.content }}</p>
                <p class="filler">此處為史料記載之模擬文本內容。當時之社會風貌、政令宣導及各界聞訊皆詳載於此。</p>
              </div>
            </div>
          </div>

          <!-- Magnifier Visual Ring -->
          <div v-if="showMagnifier" class="magnifier-ring" 
               :style="{ left: mouseX + 'px', top: mouseY + 'px' }">
          </div>

        </div>
        
        <div v-else class="table-hint">
          <!-- Text hint can be subtle or removed for realism, keeping it subtle -->
        </div>
      </div>
      
      <!-- Panel fixed to the right side of the screen, not the table, for better readability -->
      <div v-if="paper" class="modern-reader-panel">
        <div class="panel-header">【 現代標楷體對照 】</div>
        <div class="panel-content">
          <div class="modern-text">
            {{ paper.title }}<br><br>
            {{ paper.content }}<br><br>
            見證了當時社會的變遷，從基隆港的興建到市街的改正，每一字每一句都承載著厚重的歷史色彩。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.table-container {
  position: absolute;
  left: 50%;
  bottom: 0%;
  transform: translateX(-50%);
  width: 45%; 
  height: 40%;
  perspective: 2000px;
  z-index: 20;
}

.memory-table {
  width: 100%;
  height: 100%;
  transform: rotateX(30deg); /* align slightly with photo table plane */
  transform-style: preserve-3d;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.table-surface {
  width: 100%;
  height: 100%;
  /* Transparent surface */
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.active-paper-wrapper {
  width: 80%;
  height: 90%;
  /* Physical paper look */
  transform: translateZ(10px);
  position: relative;
}

.newspaper-flat {
  width: 100%;
  height: 100%;
  background: #f4ecd8;
  padding: 30px;
  color: #333;
  display: flex;
  flex-direction: column;
  position: absolute; /* Stacked */
  inset: 0;
  border: 1px solid #d3c6a6;
  overflow: hidden;
}

/* Base Layer Styles */
.base-layer {
  filter: blur(1.5px) sepia(0.6) contrast(0.9);
  pointer-events: all; /* Capture mouse */
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: url('https://www.transparenttextures.com/patterns/paper-fibers.png');
    opacity: 0.5;
    pointer-events: none;
  }
}

/* Sharp Layer Styles */
.sharp-layer {
  filter: contrast(1.2) brightness(1.05); /* Enhanced */
  background: #fff8e1; /* Lighter */
  pointer-events: none; /* Let clicks pass to base for Close Btn */
  z-index: 5;
  
  /* Hide the close button on sharp layer to avoid double button visual */
  .close-btn { display: none; }
}

.magnifier-ring {
  position: absolute;
  width: 160px; /* 80px radius * 2 */
  height: 160px;
  border: 4px solid #333;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  box-shadow: 0 5px 20px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.2);
  z-index: 10;
  
  &::after { /* Handle */
    content: '';
    position: absolute;
    bottom: -10px;
    right: -10px;
    width: 20px;
    height: 40px;
    background: #5d4037;
    transform: rotate(-45deg);
    z-index: -1;
  }
}

.newspaper-header {
  border-bottom: 3px double #333;
  text-align: center;
  margin-bottom: 10px;
  h1 { font-size: 2rem; margin-bottom: 5px; }
}

.newspaper-body {
  flex-grow: 1;
  overflow: hidden;
  h2 { font-size: 1.4rem; margin-bottom: 10px; border-bottom: 1px solid #666; }
  p { line-height: 1.4; font-size: 1rem; margin-bottom: 10px; }
  .filler { opacity: 0.5; font-style: italic; font-size: 0.8rem; }
}

.close-btn {
  position: absolute;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 30px;
  background: #8b0000;
  color: white;
  border-radius: 20px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  font-size: 1.1rem;
  cursor: pointer;
  z-index: 20; /* Ensure clickable */
  
  &:hover { background: #a00000; }
}

/* Fixed Panel for better UX */
.modern-reader-panel {
  position: fixed;
  top: 10%;
  right: 5%;
  width: 300px;
  height: 60vh;
  background: rgba(255, 255, 255, 0.95);
  border-left: 8px solid #8b0000;
  box-shadow: -5px 5px 20px rgba(0,0,0,0.3);
  z-index: 100;
  transform: none; /* Reset 3D context */
  display: flex;
  flex-direction: column;
  border-radius: 4px;
}

.panel-header {
  background: #8b0000;
  color: white;
  padding: 15px;
  font-weight: bold;
  font-size: 1.2rem;
}

.panel-content {
  padding: 20px;
  flex-grow: 1;
  overflow-y: auto;
  .modern-text {
    font-family: '楷體', 'BiauKai', 'Noto Serif TC', serif;
    font-size: 1.5rem;
    font-weight: bold;
    line-height: 2.0;
    color: #333;
  }
}
</style>
