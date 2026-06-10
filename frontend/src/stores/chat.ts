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

      let currentEvent = '';

      while (true) {
        const data = await reader.read();
        const { done, value } = data;
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          console.error('line:', line)
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const jsonStr = line.slice(5).trim();
            if (!jsonStr || jsonStr === '[DONE]') continue;

            try {
              const event = JSON.parse(jsonStr);

              if (currentEvent === 'thinking') {
                currentSkill.value = {
                  skillId: 'thinking',
                  skillName: '思考中',
                  progress: event.content || '正在分析...',
                };
              } else if (currentEvent === 'skill_selected') {
                currentSkill.value = {
                  skillId: event.skill_id,
                  skillName: event.skill_name,
                  progress: '准备执行...',
                };
              } else if (currentEvent === 'tool_calls') {
                if (currentSkill.value) {
                  currentSkill.value.progress = `调用工具: ${event.calls?.map((c: any) => c.tool).join(', ') || ''}`;
                }
              } else if (currentEvent === 'skill_completed') {
                currentSkill.value = null;
              } else if (currentEvent === 'done') {
                if (event.operations?.length) {
                  pendingOperations.value = event.operations as AIOperation[];
                }
              } else if (currentEvent === 'message') {
                assistantContent += event.content || '';
                assistantMsg.content = assistantContent;
              } else if (currentEvent === 'error') {
                assistantContent += `\n\n错误: ${event.content || event.message || '未知错误'}`;
                assistantMsg.content = assistantContent;
              }
            } catch {
              // 忽略解析错误
            }

            currentEvent = '';
          } else if (line.trim() === '') {
            // 空行表示事件结束
            currentEvent = '';
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
