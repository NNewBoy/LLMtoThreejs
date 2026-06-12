<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useCabinetStore } from './stores/cabinet';
import ThreeCanvas from './components/ThreeCanvas.vue';
import RightPanel from './components/RightPanel.vue';

const store = useCabinetStore();
const fps = ref(0);

onMounted(() => {
  store.createDefaultCabinet();

  const handleKeydown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'z') {
      e.preventDefault();
      store.undo();
    } else if (e.ctrlKey && e.key === 'y') {
      e.preventDefault();
      store.redo();
    } else if (e.key === 'Delete' && store.selectedComponentId !== null) {
      e.preventDefault();
      store.removeComponent(store.selectedComponentId);
    }
  };
  window.addEventListener('keydown', handleKeydown);
  onUnmounted(() => window.removeEventListener('keydown', handleKeydown));
});
</script>

<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <span class="logo">CabinetCraft</span>
        <input
          v-if="store.cabinet"
          class="cabinet-name"
          :value="store.cabinet.name"
          @input="store.cabinet.name = ($event.target as HTMLInputElement).value; store.isDirty = true"
        />
      </div>
      <div class="header-center">
        <button class="btn" :disabled="!store.snapshotManager.canUndo()" @click="store.undo()">撤销</button>
        <button class="btn" :disabled="!store.snapshotManager.canRedo()" @click="store.redo()">重做</button>
        <span class="separator" />
        <button class="btn" :disabled="!store.isDirty" @click="store.saveCabinet()">保存</button>
        <button class="btn" @click="store.loadCabinet(1)">加载</button>
        <button class="btn" @click="store.refreshCabinet()">刷新</button>
      </div>
      <div class="header-right">
        <span class="status-dot" :class="{ dirty: store.isDirty }" />
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- 3D Canvas Area -->
      <div class="canvas-area">
        <ThreeCanvas @update:fps="fps = $event" />
        <div class="toolbar">
          <button
            class="btn btn-sm"
            :class="{ active: store.viewMode === 'exploded' }"
            @click="store.viewMode = store.viewMode === 'exploded' ? 'normal' : 'exploded'"
          >
            爆炸视图
          </button>
          <button
            class="btn btn-sm"
            :class="{ active: store.viewMode === 'xray' }"
            @click="store.viewMode = store.viewMode === 'xray' ? 'normal' : 'xray'"
          >
            透视模式
          </button>
          <button class="btn btn-sm" @click="store.viewMode = 'normal'">重置</button>
        </div>
      </div>

      <!-- Right Panel -->
      <RightPanel />
    </div>

    <!-- Status Bar -->
    <footer class="status-bar">
      <span>板件: {{ store.sortedComponents.length }}</span>
      <span v-if="store.cabinet">
        柜体: {{ store.cabinet.width }}×{{ store.cabinet.height }}×{{ store.cabinet.depth }}mm
      </span>
      <span>FPS: {{ fps }}</span>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a2e;
  color: #e0e0e0;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  background: #16213e;
  border-bottom: 1px solid #2a2a4a;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-weight: 700;
  font-size: 16px;
  color: #7c83ff;
}

.cabinet-name {
  background: transparent;
  border: 1px solid #3a3a5a;
  color: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  width: 160px;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 6px;
}

.separator {
  width: 1px;
  height: 20px;
  background: #3a3a5a;
  margin: 0 4px;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
}

.status-dot.dirty {
  background: #f59e0b;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.canvas-area {
  flex: 1;
  position: relative;
}

.toolbar {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  gap: 6px;
  z-index: 10;
}

.btn {
  background: #2a2a4a;
  border: 1px solid #3a3a5a;
  color: #e0e0e0;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn:hover:not(:disabled) {
  background: #3a3a5a;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.btn.active {
  background: #7c83ff;
  border-color: #7c83ff;
  color: #fff;
}

.status-bar {
  display: flex;
  gap: 24px;
  padding: 4px 16px;
  background: #16213e;
  border-top: 1px solid #2a2a4a;
  font-size: 12px;
  color: #666;
}
</style>
