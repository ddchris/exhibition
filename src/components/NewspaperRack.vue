<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps(['currentActive']);
const emit = defineEmits(['select-paper']);

const isHovered = ref(false);
const isFlying = ref(false);
const flyState = ref('idle'); // idle, flying, open

const dynamicStartX = ref(0);
const dynamicStartY = ref(0);
const dynamicTargetX = ref(0); // 桌面中心 X
const dynamicTargetY = ref(0); // 桌面中心 Y
const dynamicPath = ref('');

// 報架原始座標 (1024x1024 基準)
const rawRackCoords = [
  [6, 222], [49, 656], [54, 668], [83, 646], [99, 640], [104, 630], [100, 611], 
  [106, 605], [161, 573], [208, 569], [209, 557], [166, 256], [162, 252], 
  [140, 249], [117, 240], [93, 223], [79, 222], [64, 229], [39, 229], [25, 222]
];

// 書桌區域原始座標 (1024x1024 基準，對應照片中的桌面範圍)
const rawTableCoords = [
  [100, 680], [924, 680], [1024, 1024], [0, 1024]
];



const currentPage = ref(0); // 0: Cover, 1: Spread 1 (P1/P2), 2: Spread 2 (P3/P4), 3: Spread 3 (P5/P6)
const isInFlipZone = ref(false); // 是否在翻頁熱區
const isMagnifying = ref(false);
const activeSide = ref(''); // 'cover', 'left', 'right'
const magX = ref(0);
const magY = ref(0);
const magRelX = ref(0);
const magRelY = ref(0);
const mouseX = ref(0);
const mouseY = ref(0);

const handleMouseMove = (e) => {
    if (!isFlying.value) {
        mouseX.value = e.clientX;
        mouseY.value = e.clientY;
    }
};

const clickSound = new Audio('/sounds/page-flip.mp3');

const pages = [
  { title: '臺灣日日新報', subtitle: '大正二年 八月五日', content: '孫中山先生今日抵達基隆港，大批民眾湧向港口瞻仰這位現代化領袖的風采。市街改正計畫計畫亦於昨日通過，臺北城風貌即將迎來蛻變。' },
  { title: '社會各界聞訊', subtitle: '基隆築港工事', content: '基隆港第二期築港工事正如火如荼進行中。此回擴建預計將浚挖港池、修築數座現代碼頭，完工後將成為東南亞最重要的物資轉運中心。' },
  { title: '文化采風', subtitle: '大稻埕茶香', content: '本島茶葉出口貿易再創新高。大稻埕碼頭旁各茶行商號林立，除了傳統烏龍，更有新引進的技術研發出的精品茶葉，遠銷歐美、揚名國際。' },
  { title: '城市進化', subtitle: '電力普及計畫', content: '臺灣電力株式會社宣布，為配合市街改正，城內重要幹道將全面鋪設夜間照明。入夜後的臺北街頭，在電燈的照耀下將猶如不夜之城。' },
  { title: '民生要事', subtitle: '公共場所衛生', content: '總督府衛生警察提醒市民，夏季蚊蟲繁盛。應配合環境清理與下水道排水整治，以降低熱帶疾病之傳染風險，保障全島居民健康。' },
  { title: '廣告與資訊', subtitle: '新式百貨試營業', content: '西門町一帶近期出現數家引進日式與歐風的新式商舖。其引進的精緻工藝品與海外雜貨，成為城中富裕人家相繼探訪、追求時尚的首選。' },
  { title: '教育新篇', subtitle: '國語學校擴建', content: '為推廣新式教育，臺北國語學校今日宣佈將增設教室與技藝補習班，提供本島青年更多進修機會，期能培育各界所需之優秀人才。' },
  { title: '交通動態', subtitle: '縱貫鐵路增班', content: '隨商貿繁榮，鐵路部宣佈由下月起，北高直達列車將每日增開一往返班次，並引進更舒適的水合式客車廂，提升旅客乘坐體驗。' }
];

const calculateDynamicState = () => {
    const vW = window.innerWidth;
    const vH = window.innerHeight;
    const sourceDim = 1024;

    const scale = Math.max(vW / sourceDim, vH / sourceDim);
    const offsetX = (vW - sourceDim * scale) / 2;
    const offsetY = (vH - sourceDim * scale) / 2;

    const points = rawRackCoords.map(([x, y]) => {
        const nx = x * scale + offsetX;
        const ny = y * scale + offsetY;
        return { x: nx, y: ny, str: `${nx.toFixed(1)},${ny.toFixed(1)}` };
    });
    dynamicPath.value = `M ${points.map(p => p.str).join(' L ')} Z`;

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);
    dynamicStartX.value = (Math.min(...xs) + Math.max(...xs)) / 2;
    dynamicStartY.value = (Math.min(...ys) + Math.max(...ys)) / 2;

    const tablePoints = rawTableCoords.map(([x, y]) => {
        return { x: x * scale + offsetX, y: y * scale + offsetY };
    });
    const txs = tablePoints.map(p => p.x);
    const tys = tablePoints.map(p => p.y);
    dynamicTargetX.value = (Math.min(...txs) + Math.max(...txs)) / 2;
    // Move up further to ensure bottom buttons are clearly visible
    dynamicTargetY.value = (Math.min(...tys) + Math.max(...tys)) / 2 - (vH * 0.18);
};

const handlePaperMouseMove = (e) => {
    if (flyState.value !== 'open') return;
    
    e.stopPropagation();

    const container = e.currentTarget;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    magX.value = x;
    magY.value = y;

    // 翻頁熱區檢測 (再次擴大範圍以確保完全不遮擋按鈕鄰近區域)
    const isRightFlipZone = (x > 400 && y > 220);
    const isLeftFlipZone = (x < 300 && y > 220);
    
    if (isRightFlipZone || isLeftFlipZone) {
        isInFlipZone.value = true;
        isMagnifying.value = false;
    } else {
        isInFlipZone.value = false;
    }

    // 定位邏輯 - 只有在非翻頁區才顯示放大鏡
    if (!isInFlipZone.value) {
        if (currentPage.value === 0) {
            if (x > 150 && x < 550 && y > 20 && y < 460) {
                isMagnifying.value = true;
                activeSide.value = 'cover';
                const mContainer = container.querySelector('.front .magnifier-container');
                if (mContainer) {
                    const mRect = mContainer.getBoundingClientRect();
                    magRelX.value = e.clientX - mRect.left;
                    magRelY.value = e.clientY - mRect.top;
                }
            } else {
                isMagnifying.value = false;
            }
        } else {
            // Left Page Zone (Including the flipped back cover)
            if (x >= 0 && x <= 350 && y > 20 && y < 460) {
                isMagnifying.value = true;
                activeSide.value = 'left';
                // Try to find the active left container (could be side.back or left-page)
                const mContainer = container.querySelector('.side.back .magnifier-container') || container.querySelector('.left-page .magnifier-container');
                if (mContainer) {
                    const mRect = mContainer.getBoundingClientRect();
                    magRelX.value = e.clientX - mRect.left;
                    magRelY.value = e.clientY - mRect.top;
                }
            } 
            // Right Page Zone
            else if (x > 351 && x <= 700 && y > 20 && y < 460) {
                isMagnifying.value = true;
                activeSide.value = 'right';
                const mContainer = container.querySelector('.right-page .magnifier-container');
                if (mContainer) {
                    const mRect = mContainer.getBoundingClientRect();
                    magRelX.value = e.clientX - mRect.left;
                    magRelY.value = e.clientY - mRect.top;
                }
            } else {
                isMagnifying.value = false;
            }
        }
    }
};

const flipNext = () => {
    if (currentPage.value < 4) { // 擴充至 4 個跨頁以顯示 8 頁內容
        clickSound.currentTime = 0;
        clickSound.play().catch(() => {});
        currentPage.value++;
    }
};

const flipPrev = () => {
    if (currentPage.value > 0) {
        clickSound.currentTime = 0;
        clickSound.play().catch(() => {});
        currentPage.value--;
    }
};

const triggerFlight = () => {
  if (isFlying.value) return;
  currentPage.value = 0;
  isFlying.value = true;
  flyState.value = 'idle';
  clickSound.volume = 0.5;
  clickSound.currentTime = 0;
  clickSound.play().catch(() => {});
  
  // 開始飛行動畫
  setTimeout(() => {
    flyState.value = 'flying';
  }, 50);
  
  // 飛到桌上後打開
  setTimeout(() => {
    flyState.value = 'open';
    emit('select-paper', { paper: pages[0], rect: null }); 
  }, 2550);
};

const paperActor = ref(null);

const resetFlight = () => {
    if (!isFlying.value) return;
    
    isMagnifying.value = false;
    emit('select-paper', { paper: null, rect: null }); 

    // 如果不是首頁，先執行關上動畫
    let closeDelay = 0;
    if (currentPage.value > 0) {
        currentPage.value = 0;
        closeDelay = 800; // 等待翻頁回到封面的動畫時間
        clickSound.currentTime = 0;
        clickSound.play().catch(() => {});
    }
    
        // 延遲執行飛回動畫
    setTimeout(() => {
        const el = paperActor.value;
        if (!el) {
            isFlying.value = false;
            return;
        }

        // 停止漂浮動畫，避免衝突
        el.style.animation = 'none';

        // 1. 獲取當前位置 (包含漂浮偏移)
        const computedStyle = window.getComputedStyle(el);
        const startTransform = computedStyle.transform;
        const startOpacity = computedStyle.opacity;

        // 2. 定義目標位置 (報架)
        const targetX = dynamicStartX.value;
        const targetY = dynamicStartY.value;
        const targetTransform = `translate(${targetX}px, ${targetY}px) translate(-50%, -50%) scale(0.01) rotateX(0deg) rotateY(0deg)`;

        // 3. 執行 WAAPI 動畫
        const animation = el.animate([
            { transform: startTransform, opacity: startOpacity },
            { transform: targetTransform, opacity: 0 }
        ], {
            duration: 2500,
            easing: 'cubic-bezier(.22,.61,.36,1)',
            fill: 'forwards'
        });

        animation.onfinish = () => {
             isFlying.value = false;
             flyState.value = 'idle';
             el.style.animation = ''; // 清除 inline style
        };

    }, closeDelay);
};

onMounted(() => {
  calculateDynamicState();
  window.addEventListener('resize', calculateDynamicState);
  window.addEventListener('mousemove', handleMouseMove);
});

onUnmounted(() => {
  window.removeEventListener('resize', calculateDynamicState);
  window.removeEventListener('mousemove', handleMouseMove);
});
</script>

<template>
  <div class="rack-overlay">
    
    <svg class="dynamic-svg-layer">
      <g 
        id="newspaper-rack-trigger"
        class="interactive-group"
        @mouseenter="isHovered = true"
        @mouseleave="isHovered = false"
        @click="triggerFlight"
      >
        <path 
          :d="dynamicPath" 
          class="rack-path"
          :class="{ 'is-hovered': isHovered && !isFlying }"
        />
      </g>
    </svg>

    <div 
      v-if="isHovered && !isFlying" 
      class="cursor-tooltip"
      :style="{ top: mouseY + 15 + 'px', left: mouseX + 15 + 'px' }"
    >
      <span class="icon">📰</span> 開始閱讀報紙
    </div>

    <!-- 3D 報紙演員 -->
    <!-- Transition removed -->
    <!-- 3D 報紙演員 -->
    <!-- Transition removed -->
      <div 
        v-if="isFlying" 
        ref="paperActor"
        class="paper-actor-container"
        :class="{ 
          'fly-in': flyState === 'flying' || flyState === 'open',
          'open': flyState === 'open',
          'is-pointing': isInFlipZone
        }"
        @mousemove="handlePaperMouseMove"
        :style="{ 
          '--start-x': dynamicStartX + 'px', 
          '--start-y': dynamicStartY + 'px',
          '--target-x': dynamicTargetX + 'px',
          '--target-y': dynamicTargetY + 'px'
        }"
      >
        <div class="book-container" :class="{ 'is-closed': currentPage === 0 }">
          
          <!-- 左側固定頁 ... (中間內容不變，略過以縮短 chunk) ... -->
          <!-- 此處內容與原始代碼一致 -->
          <div class="book-page left-page" v-if="currentPage > 0">
              <div class="page-inner">
                  <div class="paper-texture"></div>
                  <div class="spine-shadow left"></div>
                  <div class="paper-content">
                      <div class="newspaper-header" style="opacity: 0.8;">
                          <h2 style="font-size: 1.4rem;">{{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].title : '扉頁' }}</h2>
                          <div class="divider grey-divider"></div>
                      </div>
                      <div class="magnifier-container">
                           <div class="excerpt-view old-view">{{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].content : '' }}</div>
                           <div 
                              class="excerpt-view clear-view"
                              v-if="isMagnifying && activeSide === 'left'"
                              :style="{ 
                                  'clip-path': `circle(57px at ${magRelX}px ${magRelY}px)`,
                                  'transform': `translate(${magRelX * (1 - 1.58)}px, ${magRelY * (1 - 1.58)}px) scale(1.58)` 
                              }"
                           >
                              {{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].content : '' }}
                           </div>
                      </div>
                  </div>
                  <div class="page-num">第 {{ currentPage * 2 - 1 }} 頁</div>
                  <div class="flip-hint-wrapper left-hint" @click.stop="flipPrev">
                      <div class="flip-arrow"><<</div>
                      <span class="flip-text">返回前頁</span>
                  </div>
              </div>
          </div>

          <div class="book-page right-page" v-show="currentPage > 0">
              <div class="page-inner">
                  <div class="paper-texture"></div>
                  <div class="spine-shadow right"></div>
                  <div class="paper-content">
                      <div class="newspaper-header">
                          <h2>{{ pages[currentPage * 2] ? pages[currentPage * 2].title : '未完待續' }}</h2>
                          <div class="divider"></div>
                          <p class="year-label">{{ pages[currentPage * 2] ? pages[currentPage * 2].subtitle : '' }}</p>
                      </div>
                      <div class="magnifier-container">
                          <div class="excerpt-view old-view">{{ pages[currentPage * 2] ? pages[currentPage * 2].content : '' }}</div>
                          <div 
                              class="excerpt-view clear-view"
                              v-if="isMagnifying && activeSide === 'right'"
                              :style="{ 
                                  'clip-path': `circle(57px at ${magRelX}px ${magRelY}px)`,
                                  'transform': `translate(${magRelX * (1 - 1.58)}px, ${magRelY * (1 - 1.58)}px) scale(1.58)` 
                              }"
                          >
                              {{ pages[currentPage * 2] ? pages[currentPage * 2].content : '' }}
                          </div>
                      </div>
                  </div>
                  <div class="page-num">第 {{ currentPage * 2 }} 頁</div>
                  <div v-if="currentPage < 4" class="flip-hint-wrapper" @click.stop="flipNext">
                      <span class="flip-text">繼續閱讀</span>
                      <div class="flip-arrow">>></div>
                  </div>
              </div>
          </div>

          <div class="book-page flip-page" :class="{ 'flipped': currentPage > 0 }" @click="currentPage === 0 ? flipNext() : null">
              <div class="side front">
                  <div class="page-inner">
                      <div class="paper-texture"></div>
                      <div class="paper-content">
                          <div class="newspaper-header">
                              <h2 style="font-size: 1.8rem;">{{ pages[0].title }}</h2>
                              <div class="divider"></div>
                              <p class="year-label">{{ pages[0].subtitle }}</p>
                          </div>
                          <div class="magnifier-container">
                               <div class="excerpt-view old-view">{{ pages[0].content }}</div>
                               <div 
                                  class="excerpt-view clear-view"
                                  v-if="isMagnifying && activeSide === 'cover'"
                                  :style="{ 
                                      'clip-path': `circle(57px at ${magRelX}px ${magRelY}px)`,
                                      'transform': `translate(${magRelX * (1 - 1.58)}px, ${magRelY * (1 - 1.58)}px) scale(1.58)` 
                                  }"
                               >
                                  {{ pages[0].content }}
                               </div>
                          </div>
                      </div>
                  </div>
                  <div v-show="currentPage === 0" class="flip-hint-wrapper" @click.stop="flipNext">
                      <span class="flip-text">點擊翻閱報導</span>
                      <div class="flip-arrow">>></div>
                  </div>
              </div>
              <div class="side back">
                  <div class="page-inner">
                      <div class="paper-texture"></div>
                      <div class="spine-shadow left"></div>
                      <div class="paper-content">
                          <div class="newspaper-header" style="opacity: 0.8;">
                               <h2 style="font-size: 1.4rem;">{{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].title : '扉頁' }}</h2>
                               <div class="divider grey-divider"></div>
                          </div>
                          <div class="magnifier-container">
                               <div class="excerpt-view old-view">
                                  {{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].content : '' }}
                               </div>
                               <div 
                                  class="excerpt-view clear-view"
                                  v-if="isMagnifying && activeSide === 'left'"
                                  :style="{ 
                                      'clip-path': `circle(57px at ${magRelX}px ${magRelY}px)`,
                                      'transform': `translate(${magRelX * (1 - 1.58)}px, ${magRelY * (1 - 1.58)}px) scale(1.58)` 
                                  }"
                               >
                                  {{ pages[currentPage * 2 - 1] ? pages[currentPage * 2 - 1].content : '' }}
                               </div>
                          </div>
                      </div>
                      <div class="page-num">第 {{ currentPage * 2 - 1 }} 頁</div>
                      <div class="flip-hint-wrapper left-hint" @click.stop="flipPrev">
                          <div class="flip-arrow"><<</div>
                          <span class="flip-text">返回前頁</span>
                      </div>
                  </div>
              </div>
          </div>
        </div>
        
        <div 
          v-if="isMagnifying && !isInFlipZone" 
          class="cute-magnifier" 
          :style="{ left: magX + 'px', top: magY + 'px' }"
        >
          <div class="magnifier-body">
              <div class="magnifier-rim"></div>
              <div class="magnifier-handle"></div>
          </div>
        </div>

        <div v-if="flyState === 'open'" class="close-newspaper" @click.stop="resetFlight">
            <span class="icon">✕</span> 放置一旁
        </div>
      </div>
    <!-- Transition removed -->
    
    <!-- 互動遮罩 -->
    <div v-if="flyState === 'open'" class="interaction-blocker" @click="resetFlight"></div>

  </div>
</template>

<style scoped>
.rack-overlay {
  position: fixed;
  inset: 0;
  pointer-events: none; 
  z-index: 25;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  caret-color: transparent;
}

.interaction-blocker {
    position: fixed;
    inset: 0;
    z-index: 40; /* 高於背景的留聲機 (30)，低於報紙 (500) */
    pointer-events: auto; /* 攔截所有鼠標事件 */
    background: transparent;
    user-select: none;
}

.dynamic-svg-layer { width: 100vw; height: 100vh; display: block; }
.interactive-group { cursor: pointer; pointer-events: auto; }
.rack-path { 
  fill: transparent; 
  stroke: transparent; 
  stroke-width: 2.5; 
  transition: all 0.4s ease; 
}
.rack-path.is-hovered {
  fill: rgba(255, 215, 0, 0.2); 
  stroke: #FFD700; 
  stroke-width: 4;
  stroke-dasharray: none;
  filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.6));
  animation: none;
}

@keyframes pulsePathRack {
  0%, 100% { stroke: rgba(255, 215, 0, 0.2); stroke-width: 2; }
  50% { stroke: rgba(255, 215, 0, 1); stroke-width: 3.5; }
}
.cursor-tooltip {
  position: fixed; background: rgba(0, 0, 0, 0.85); color: #FFD700;
  padding: 10px 16px; border-radius: 8px; font-size: 15px; pointer-events: none;
  backdrop-filter: blur(6px); border: 1px solid rgba(255, 215, 0, 0.3);
  z-index: 100; font-family: '楷體', serif;
}

/* --- 3D 書本桌面版核心 --- */
/* --- 3D 書本桌面版核心 --- */
.paper-actor-container {
  position: fixed;
  left: 0; top: 0;
  width: 700px;
  height: 480px;
  z-index: 500;
  opacity: 0; 
  transform-style: preserve-3d;
  /* 強制初始狀態，確保 idle 時有明確的屬性可供 transition */
  transform: translate(var(--start-x), var(--start-y)) translate(-50%, -50%) scale(0.01) rotateX(0deg) rotateY(0deg);
  transition: transform 2.5s cubic-bezier(.22,.61,.36,1), opacity 2.5s ease;
  perspective: 2500px;
  pointer-events: none;
  user-select: none;
}

.paper-actor-container.fly-in {
  opacity: 1;
  transform: translate(var(--target-x), var(--target-y)) translate(-50%, -100%) scale(0.9) rotateX(15deg) rotateY(0deg);
  pointer-events: auto; /* 開啟時捕捉所有滑鼠事件 */
}

.paper-actor-container.open {
  transform: translate(var(--target-x), var(--target-y)) translate(-50%, -100%) scale(1.0) rotateX(25deg);
  animation: tableFloat 5s ease-in-out infinite;
}

/* 手指游標控制 */
.paper-actor-container.is-pointing {
    cursor: pointer !important;
}

.book-container {
  width: 100%; height: 100%;
  position: relative;
  transform-style: preserve-3d;
  display: flex;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.book-container.is-closed {
  transform: translateX(-25%);
}

.book-page {
  position: absolute;
  width: 50%; height: 100%;
  top: 0;
  background: #fdf5e6;
  border: 1px solid #d3c6a6;
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.left-page { left: 0; transform-origin: right center; border-radius: 4px 0 0 4px; z-index: 2; }
.right-page { left: 50%; transform-origin: left center; border-radius: 0 4px 4px 0; z-index: 1; }

.flip-page {
  left: 50%;
  transform-origin: left center;
  z-index: 5;
  cursor: pointer;
  pointer-events: none; /* Allow events to pass to fixed layers underneath */
}
.flip-page.flipped { transform: rotateY(-180deg); }

.flip-page .side {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  background: #fdf5e6;
  box-shadow: inset 0 0 30px rgba(0,0,0,0.02);
  pointer-events: auto; /* Buttons on the flipping surface remain clickable */
}
.flip-page .side.back { 
  transform: rotateY(180deg); 
}

/* Ensure the invisible side doesn't block the visible layers beneath */
.flip-page.flipped .side.front { 
  pointer-events: none;
  visibility: hidden; /* Extra safety */
}
.flip-page:not(.flipped) .side.back {
  pointer-events: none;
  visibility: hidden;
}

.page-inner {
  width: 100%; height: 100%;
  position: relative; padding: 25px 30px;
  display: flex; flex-direction: column;
}

/* --- 萬能放大鏡校正 --- */
.magnifier-container {
    position: relative;
    width: 100%;
    height: 180px;
    margin-top: 10px;
}

.excerpt-view {
    position: absolute;
    inset: 0;
    font-family: '楷體', serif;
    text-align: justify;
    user-select: none;
}

.old-view {
    font-size: 0.95rem;
    line-height: 1.6;
    color: rgba(0,0,0,0.7);
    filter: blur(1.5px) sepia(0.3);
}

.clear-view {
    font-size: 0.95rem; /* Reset to match old-view for consistent wrapping */
    line-height: 1.6;
    color: #000 !important;
    font-family: 'BiauKai', '標楷體', serif;
    font-weight: 700;
    pointer-events: none;
    z-index: 20;
    background: #fdf5e6;
    white-space: normal;
    transform-origin: 0 0; /* Important for scale calibration */
}

/* --- 翻頁提示組件 (Restored & Styled like HUD) --- */
.flip-hint-wrapper {
    position: absolute;
    bottom: 60px; /* Moved up to avoid any potential overlap */
    right: 30px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: '楷體', serif;
    font-size: 1rem;
    font-weight: 900;
    color: #fdf5e6;
    background: rgba(45, 52, 54, 0.95); /* Slightly clearer background */
    padding: 10px 24px; /* Larger touch target */
    border-radius: 30px;
    cursor: pointer;
    z-index: 1000; /* Force z-index high */
    pointer-events: auto !important; /* Force clickability */
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.25);
    transition: transform 0.2s, background 0.2s;
    min-width: 140px; /* Ensure hit area */
    justify-content: center;
}

.flip-hint-wrapper:hover {
    transform: scale(1.05);
    background: rgba(45, 52, 54, 1);
}

.left-hint {
    right: auto;
    left: 30px;
    flex-direction: row-reverse;
}

.page-num {
    position: absolute;
    bottom: 70px; /* Moved up proportional to button */
    font-size: 0.9rem;
    font-weight: bold;
    color: #333;
    opacity: 0.7;
    z-index: 900;
}

/* Page Num Positioning */
.left-page .page-num, .side.back .page-num { left: auto; right: 30px; } /* Opposite to button */
.right-page .page-num { right: auto; left: 30px; } /* Opposite to button */

.flip-arrow {
    font-weight: 900;
    font-size: 1.2rem;
    animation: arrowPulse 1.5s infinite;
}

@keyframes arrowPulse {
    0%, 100% { transform: translateX(0); opacity: 0.6; }
    50% { transform: translateX(5px); opacity: 1; }
}

/* --- 可愛版放大鏡 --- */
.cute-magnifier {
    position: absolute;
    pointer-events: none;
    z-index: 100;
    transform: translate(-90px, -90px);
}

.magnifier-body {
    position: relative;
    width: 200px;
    height: 200px;
}

.magnifier-rim {
    width: 180px;
    height: 180px;
    border-radius: 50%;
    border: 8px solid #2d3436;
    background: rgba(255, 255, 255, 0.1);
    box-shadow: 
        0 10px 25px rgba(0,0,0,0.3),
        inset 0 0 15px rgba(255,255,255,0.4);
    position: relative;
    overflow: hidden;
}


.magnifier-handle {
    position: absolute;
    width: 25px;
    height: 80px;
    background: #d35400;
    border: 4px solid #2d3436;
    border-radius: 12px;
    bottom: -15px;
    right: 5px;
    transform: rotate(-45deg);
    box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
}

.spine-shadow { position: absolute; top: 0; bottom: 0; width: 40px; pointer-events: none; z-index: 10; }
.spine-shadow.left { right: 0; background: linear-gradient(90deg, transparent, rgba(0,0,0,0.08)); }
.spine-shadow.right { left: 0; background: linear-gradient(-90deg, transparent, rgba(0,0,0,0.08)); }

.paper-texture { position: absolute; inset: 0; background-image: url('https://www.transparenttextures.com/patterns/paper-fibers.png'); opacity: 0.3; pointer-events: none; }
.paper-content { position: relative; z-index: 1; color: #000 !important; }
.newspaper-header h2 { font-family: '楷體', serif; font-size: 1.8rem; color: #000 !important; font-weight: 900; }
.divider { height: 3px; background-color: #000 !important; margin: 8px 0; border: none; }
.grey-divider { background-color: rgba(0,0,0,0.2) !important; height: 1px !important; margin: 10px 0 !important; }
.year-label { font-size: 1rem; font-weight: 900; color: #000 !important; }
/* Page Num adjustment */

.close-newspaper {
  position: absolute;
  top: -40px; /* Move to the top of the paper instead of bottom */
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.7);
  color: #fff;
  padding: 8px 24px;
  border-radius: 25px;
  cursor: pointer;
  pointer-events: auto;
  font-size: 1rem;
  transition: all 0.3s;
  z-index: 1000;
  border: 1px solid rgba(255,255,255,0.2);
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.close-newspaper:hover {
    background: rgba(0,0,0,0.9);
    transform: translateX(-50%) scale(1.05);
}

@keyframes tableFloat {
  0%, 100% { transform: translate(var(--target-x), var(--target-y)) translate(-50%, -100%) scale(1.0) rotateX(25deg); }
  50% { transform: translate(var(--target-x), var(--target-y)) translate(-50%, -100%) scale(1.0) rotateX(23deg) translateY(-2px); }
}
</style>
