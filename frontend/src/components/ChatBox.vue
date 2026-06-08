<template>
  <div class="chat-container">
    <div class="messages-area" ref="messagesRef">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">💬</div>
        <h2>您好！有什么可以帮助您的？</h2>
        <p class="welcome-hint">在下方的输入框中输入您的问题，我将为您解答。</p>
      </div>

      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['message', msg.role === 'user' ? 'message-user' : 'message-assistant']"
      >
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-content">
          <div class="message-bubble" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>

      <div v-if="loading" class="message message-assistant">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="message-bubble thinking">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          @keydown.enter.exact="sendMessage"
          placeholder="输入您的问题，按 Enter 发送..."
          rows="1"
          ref="inputRef"
          :disabled="loading"
        ></textarea>
        <button
          class="send-btn"
          @click="sendMessage"
          :disabled="!inputText.trim() || loading"
        >
          <span v-if="!loading">发送</span>
          <span v-else>...</span>
        </button>
      </div>
      <p class="input-tip">Shift+Enter 换行</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from "vue";
import axios from "axios";
import { marked } from "marked";

const messages = ref([]);
const inputText = ref("");
const loading = ref(false);
const messagesRef = ref(null);
const inputRef = ref(null);

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
});

function renderMarkdown(text) {
  return marked.parse(text);
}

async function sendMessage(e) {
  if (e && e.shiftKey) return;
  const text = inputText.value.trim();
  if (!text || loading.value) return;

  // 添加用户消息
  messages.value.push({ role: "user", content: text });
  inputText.value = "";
  loading.value = true;
  scrollToBottom();

  try {
    // 构建历史消息
    const history = messages.value
      .filter((m) => m.role !== "system")
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }));

    const res = await axios.post("/api/chat/", {
      message: text,
      history: history,
    });

    messages.value.push({
      role: "assistant",
      content: res.data.reply,
    });
  } catch (err) {
    const errorMsg =
      err.response?.data?.error || "服务暂时不可用，请稍后重试";
    messages.value.push({
      role: "assistant",
      content: `❌ **抱歉，出错了**\n\n${errorMsg}`,
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
    }
  });
}

onMounted(() => {
  inputRef.value?.focus();
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 800px;
  height: calc(100vh - 160px);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.messages-area::-webkit-scrollbar {
  width: 6px;
}

.messages-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

/* 欢迎界面 */
.welcome {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.6);
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome h2 {
  font-size: 22px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
}

.welcome-hint {
  font-size: 14px;
}

/* 消息 */
.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-assistant {
  align-self: flex-start;
}

.message-avatar {
  font-size: 28px;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 50%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message-user .message-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-assistant .message-bubble {
  background: rgba(255, 255, 255, 0.08);
  color: #e0e0e0;
  border-bottom-left-radius: 4px;
}

.message-bubble :deep(p) {
  margin-bottom: 8px;
}

.message-bubble :deep(p:last-child) {
  margin-bottom: 0;
}

.message-bubble :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-bubble :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-bubble :deep(pre code) {
  background: none;
  padding: 0;
}

/* 思考动画 */
.thinking {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px 20px;
}

.dot {
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入区域 */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.input-wrapper {
  display: flex;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 4px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: rgba(102, 126, 234, 0.6);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  padding: 10px 12px;
  color: #e0e0e0;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  line-height: 1.5;
  max-height: 120px;
}

textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.send-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
  align-self: flex-end;
  margin-bottom: 4px;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-tip {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.25);
  margin-top: 6px;
  padding-left: 4px;
}
</style>
