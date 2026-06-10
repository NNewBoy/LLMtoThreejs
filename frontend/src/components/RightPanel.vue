<script setup lang="ts">
import { ref } from 'vue';
import PropertyTab from './PropertyTab.vue';
import AITab from './AITab.vue';

const activeTab = ref<'properties' | 'chat'>('properties');
</script>

<template>
  <div class="right-panel">
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'properties' }"
        @click="activeTab = 'properties'"
      >
        属性编辑
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'chat' }"
        @click="activeTab = 'chat'"
      >
        AI 对话
      </button>
    </div>

    <div class="tab-content">
      <PropertyTab v-if="activeTab === 'properties'" />
      <AITab v-else />
    </div>
  </div>
</template>

<style scoped>
.right-panel {
  width: 360px;
  background: #16213e;
  border-left: 1px solid #2a2a4a;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid #2a2a4a;
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 13px;
  border-bottom: 2px solid transparent;
}

.tab-btn.active {
  color: #7c83ff;
  border-bottom-color: #7c83ff;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
</style>
