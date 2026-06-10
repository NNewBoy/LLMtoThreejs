<script setup lang="ts">
import { ref } from 'vue';
import { useCabinetStore } from '../stores/cabinet';
import { useChatStore } from '../stores/chat';

const store = useCabinetStore();
const chatStore = useChatStore();
const chatInput = ref('');

function onSendChat() {
  if (!chatInput.value.trim() || !store.cabinet) return;
  chatStore.sendMessage(store.cabinet.id, chatInput.value.trim());
  chatInput.value = '';
}

function onConfirmOps() {
  if (chatStore.pendingOperations) {
    store.applyAIOperations(chatStore.pendingOperations);
    chatStore.confirmOperations();
  }
}
</script>

<template>
  <div class="ai-tab">
    <!-- Skill Progress -->
    <div v-if="chatStore.currentSkill" class="skill-card">
      <div class="skill-icon">&#9881;</div>
      <div class="skill-info">
        <div class="skill-name">{{ chatStore.currentSkill.skillName }}</div>
        <div class="skill-progress">{{ chatStore.currentSkill.progress }}</div>
      </div>
    </div>

    <!-- Messages -->
    <div class="chat-messages">
      <div
        v-for="msg in chatStore.messages"
        :key="msg.id"
        class="chat-msg"
        :class="msg.role"
      >
        <div class="msg-content">{{ msg.content }}</div>
      </div>
      <div v-if="chatStore.isStreaming" class="chat-msg assistant streaming">
        <div class="msg-content">正在思考...</div>
      </div>
    </div>

    <!-- Pending Operations -->
    <div v-if="chatStore.pendingOperations" class="pending-ops">
      <h4>AI 操作确认</h4>
      <div v-for="(op, i) in chatStore.pendingOperations" :key="i" class="op-item">
        <span class="op-action">{{ op.action }}</span>
        <span>{{ op.label ?? op.componentType ?? '' }}</span>
      </div>
      <div class="op-actions">
        <button class="btn btn-primary btn-sm" @click="onConfirmOps">确认执行</button>
        <button class="btn btn-sm" @click="chatStore.rejectOperations()">拒绝</button>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-area">
      <input
        v-model="chatInput"
        class="chat-input"
        placeholder="描述你想要的修改..."
        @keydown.enter="onSendChat"
        :disabled="chatStore.isStreaming"
      />
      <button class="btn btn-primary" @click="onSendChat" :disabled="chatStore.isStreaming">
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.ai-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.skill-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #1a2a1a;
  border: 1px solid #4ade80;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}

.skill-icon {
  font-size: 20px;
  color: #4ade80;
}

.skill-name {
  font-size: 13px;
  font-weight: 600;
  color: #4ade80;
}

.skill-progress {
  font-size: 12px;
  color: #888;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 8px;
}

.chat-msg {
  margin-bottom: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-msg.user {
  background: #2a2a5a;
  margin-left: 24px;
}

.chat-msg.assistant {
  background: #1a1a2e;
  margin-right: 24px;
}

.chat-msg.system {
  background: #3a1a1a;
  color: #fca5a5;
  font-size: 12px;
}

.streaming .msg-content::after {
  content: '...';
  animation: blink 1s steps(3) infinite;
}

@keyframes blink {
  0% { content: '.'; }
  33% { content: '..'; }
  66% { content: '...'; }
}

.pending-ops {
  background: #1a2a1a;
  border: 1px solid #4ade80;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}

.pending-ops h4 {
  font-size: 13px;
  color: #4ade80;
  margin-bottom: 6px;
}

.op-item {
  font-size: 12px;
  padding: 4px 0;
  display: flex;
  gap: 8px;
}

.op-action {
  background: #2a2a4a;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  text-transform: uppercase;
}

.op-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.chat-input-area {
  display: flex;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid #2a2a4a;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  background: #1a1a2e;
  border: 1px solid #3a3a5a;
  color: #e0e0e0;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 13px;
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

.btn-primary {
  background: #7c83ff;
  border-color: #7c83ff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #6366f1;
}
</style>
