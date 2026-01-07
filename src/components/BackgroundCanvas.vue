<script setup>
// No script logic needed for a static GIF background
</script>

<template>
  <div class="bg-container">
    <img src="/bg_v7_hd.png" alt="Background" class="bg-image" />
  </div>
</template>

<style scoped>
.bg-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0; /* Behind everything */
  overflow: hidden;
  background: #000;
}

.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* Ensures the GIF covers the screen without stretching */
  display: block;
}
</style>
