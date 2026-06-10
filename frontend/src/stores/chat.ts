import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ChatMessage, AIOperation, SkillInfo } from '../types';

const API_BASE = '/api';

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([]);
  const isStreaming = ref(false);
  const currentSkill = ref<SkillInfo | null>(null);
  const pendingOperations = ref<AIOperation[] | null>(null);

  function addMessage(msg: ChatMessage): void {
    messages.value.push(msg);
  }

  async function sendMessage(cabinetId: number, text: string): Promise<void> {
    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    addMessage(userMsg);
    isStreaming.value = true;
    pendingOperations.value = null;

    try {
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cabinet_id: cabinetId,
          message: text,
          history: messages.value.slice(-20).map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // 处理 SSE 流
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      let assistantContent = '';

      const assistantMsg: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };
      addMessage(assistantMsg);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'skill_start') {
              currentSkill.value = {
                skillId: event.skill_id,
                skillName: event.skill_name,
                progress: '执行中...',
              };
            } else if (event.type === 'skill_end') {
              currentSkill.value = null;
            } else if (event.type === 'operations') {
              pendingOperations.value = event.operations as AIOperation[];
            } else if (event.type === 'text') {
              assistantContent += event.content;
              assistantMsg.content = assistantContent;
            } else if (event.type === 'error') {
              assistantContent += `\n\n错误: ${event.message}`;
              assistantMsg.content = assistantContent;
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    } catch (err) {
      const errMsg: ChatMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'system',
        content: `发送失败: ${err instanceof Error ? err.message : '未知错误'}`,
        timestamp: Date.now(),
      };
      addMessage(errMsg);
    } finally {
      isStreaming.value = false;
    }
  }

  function confirmOperations(): void {
    pendingOperations.value = null;
  }

  function rejectOperations(): void {
    pendingOperations.value = null;
  }

  function clearMessages(): void {
    messages.value = [];
    pendingOperations.value = null;
    currentSkill.value = null;
  }

  return {
    messages,
    isStreaming,
    currentSkill,
    pendingOperations,
    addMessage,
    sendMessage,
    confirmOperations,
    rejectOperations,
    clearMessages,
  };
});
