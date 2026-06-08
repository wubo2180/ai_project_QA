<template>
  <div class="chat-view">
    <!-- 欢迎界面 -->
    <div v-if="messages.length === 0 && !loading" class="welcome">
      <div class="welcome-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="10" fill="#1a73e8"/>
          <path d="M12 20c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8-8-3.6-8-8z" fill="white" opacity="0.9"/>
          <path d="M18 17l4 3-4 3" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </svg>
      </div>
      <h1 class="welcome-title">有什么可以帮忙的？</h1>
      <div class="suggestions">
        <div class="suggestion-item" @click="sendSuggestion('用简单的话解释什么是人工智能')">
          <span class="suggestion-icon">🧠</span>
          <span>用简单的话解释什么是人工智能</span>
        </div>
        <div class="suggestion-item" @click="sendSuggestion('帮我写一首关于夏天的诗')">
          <span class="suggestion-icon">✍️</span>
          <span>帮我写一首关于夏天的诗</span>
        </div>
        <div class="suggestion-item" @click="sendSuggestion('Python中列表和元组的区别是什么')">
          <span class="suggestion-icon">💻</span>
          <span>Python 列表和元组的区别</span>
        </div>
        <div class="suggestion-item" @click="sendSuggestion('给我一些健身建议')">
          <span class="suggestion-icon">💪</span>
          <span>给我一些健身建议</span>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div v-else class="messages-area" ref="messagesRef">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['message-row', msg.role === 'user' ? 'user-row' : 'assistant-row']"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else class="ai-avatar">AI</span>
        </div>
        <div class="message-body">
          <div class="message-name">{{ msg.role === 'user' ? '你' : 'AI 助手' }}</div>
          <!-- 用户粘贴的图片 -->
          <div v-if="msg.imageData" class="message-image">
            <img :src="'data:image/png;base64,' + msg.imageData" alt="用户图片" />
          </div>
          <div class="message-content markdown-body" v-html="renderMarkdown(msg.content)"></div>
          <div v-if="msg.role === 'assistant'" class="message-actions">
            <button v-if="msg.excelMode" class="action-btn excel-btn" @click="downloadExcel(msg.content)" title="下载 Excel">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>
            </button>
            <button class="action-btn" @click="copyMessage(msg.content)" title="复制">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 加载动画 -->
      <div v-if="loading" class="message-row assistant-row">
        <div class="message-avatar">
          <span class="ai-avatar">AI</span>
        </div>
        <div class="message-body">
          <div class="message-name">AI 助手</div>
          <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入 -->
    <div class="input-area">
      <div class="input-container">
        <div class="input-wrapper">
          <!-- 模型选择 -->
          <select class="model-select" v-model="selectedModel" :disabled="loading">
            <option v-for="(m, key) in models" :key="key" :value="key">
              {{ m.label }} ({{ m.model }})
            </option>
          </select>

          <button
            class="mode-toggle excel-toggle"
            :class="{ active: excelMode }"
            @click="excelMode = !excelMode"
            :title="excelMode ? '关闭 Excel 整理' : '开启 Excel 整理'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            <span>Excel</span>
          </button>
          <button
            class="mode-toggle search-toggle"
            :class="{ active: webSearch }"
            @click="webSearch = !webSearch"
            :title="webSearch ? '关闭网页搜索' : '开启网页搜索'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <span>搜索</span>
          </button>
          <textarea
            ref="inputRef"
            v-model="inputText"
            @keydown.enter.exact="sendMessage"
            @keydown.enter.shift="insertNewline"
            @paste="handlePaste"
            placeholder="给 AI 助手发送消息"
            rows="1"
            :disabled="loading"
          ></textarea>
          <!-- 图片预览 -->
          <div v-if="pastedImage" class="image-preview" @click="clearImage" :title="'点击移除图片'">
            <img :src="pastedImage" />
            <span class="image-remove">×</span>
          </div>
          <button
            class="send-btn"
            :class="{ active: (inputText.trim() || pastedImage) && !loading }"
            :disabled="!inputText.trim() && !pastedImage || loading"
            @click="sendMessage"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
        <p class="input-footer">
          <span v-if="pastedImage" class="image-hint">🖼️ 已粘贴图片</span>
          <template v-else-if="excelMode && webSearch">
            <span class="excel-mode-hint">📊 Excel 模式 + 🌐 搜索模式 已同时开启</span>
          </template>
          <span v-else-if="excelMode" class="excel-mode-hint">📊 Excel 整理模式已开启，AI 回复将提供表格下载</span>
          <span v-else-if="webSearch" class="search-mode-hint">🌐 网页搜索模式已开启，AI 将搜索网络获取最新信息</span>
          <span v-else-if="!currentModelSupportsImage" class="model-hint">💡 选择通义千问可粘贴图片</span>
          <span v-else>AI 助手可能会产生不准确的信息，请注意甄别。</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, computed } from "vue";
import { marked } from "marked";
import axios from "axios";

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["send"]);

const inputText = ref("");
const inputRef = ref(null);
const messagesRef = ref(null);
const excelMode = ref(false);
const webSearch = ref(false);
const selectedModel = ref("deepseek");
const models = ref({});
const pastedImage = ref(null); // base64 data URL

// 当前选择模型是否支持图片
const currentModelSupportsImage = computed(() => {
  const m = models.value[selectedModel.value];
  return m ? m.supports_image : false;
});

// 加载模型列表
onMounted(async () => {
  try {
    const res = await axios.get("/api/models/");
    models.value = res.data;
  } catch { /* ignore */ }
});

marked.setOptions({ breaks: true, gfm: true });

function renderMarkdown(text) {
  return marked.parse(text);
}

function sendMessage(e) {
  if (e && e.shiftKey) return;
  const text = inputText.value.trim();
  if ((!text && !pastedImage.value) || props.loading) return;
  emit("send", {
    text: text || "请分析这张图片",
    excelMode: excelMode.value,
    webSearch: webSearch.value,
    model: selectedModel.value,
    imageData: extractBase64(pastedImage.value),
  });
  inputText.value = "";
  pastedImage.value = null; // 发送后清除图片
  inputRef.value?.focus();
}

function sendSuggestion(text) {
  if (props.loading) return;
  emit("send", {
    text,
    excelMode: excelMode.value,
    webSearch: webSearch.value,
    model: selectedModel.value,
    imageData: null,
  });
  inputRef.value?.focus();
}

// 从 data URL 中提取纯 base64 字符串
function extractBase64(dataUrl) {
  if (!dataUrl) return null;
  const parts = dataUrl.split(",");
  return parts.length > 1 ? parts[1] : null;
}

function insertNewline(e) {
  const textarea = e.target;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  inputText.value =
    inputText.value.substring(0, start) +
    "\n" +
    inputText.value.substring(end);
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 1;
    autoResize(textarea);
  });
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

async function copyMessage(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // fallback
  }
}

function downloadExcel(content) {
  // 通过后端 API 生成并下载 Excel
  const filename = "导出数据_" + new Date().toISOString().slice(0, 10);
  
  fetch("/api/export-excel/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, filename }),
  })
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "导出失败");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    })
    .catch(() => alert("导出失败，请检查网络连接"));
}

function handlePaste(e) {
  if (!currentModelSupportsImage.value) return; // 仅 qwen 可粘贴图片
  const items = e.clipboardData.items;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      e.preventDefault();
      const file = item.getAsFile();
      if (!file) continue;
      const reader = new FileReader();
      reader.onload = (ev) => {
        pastedImage.value = ev.target.result; // data:image/png;base64,...
      };
      reader.readAsDataURL(file);
      break;
    }
  }
}

function clearImage() {
  pastedImage.value = null;
}

watch(
  () => props.messages.length,
  () => {
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
      }
    });
  }
);

watch(() => inputText.value, () => {
  nextTick(() => {
    const el = inputRef.value;
    if (el) autoResize(el);
  });
});

watch(selectedModel, (newModel) => {
  if (newModel === "ernie-bot") {
    pastedImage.value = null;
  }
});
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
}

/* ===== 欢迎界面 ===== */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.welcome-logo {
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 32px;
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-width: 560px;
  width: 100%;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f7f7f8;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
  color: #333;
  text-align: left;
}

.suggestion-item:hover {
  background: #efeff0;
  border-color: #d0d0d0;
}

.suggestion-icon {
  font-size: 18px;
  flex-shrink: 0;
}

/* ===== 消息区域 ===== */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.messages-area::-webkit-scrollbar { width: 6px; }
.messages-area::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }

.message-row {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}

.assistant-row {
  background: #fafafa;
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.ai-avatar {
  width: 32px;
  height: 32px;
  background: #1a73e8;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 6px;
}

.message-content {
  font-size: 15px;
  line-height: 1.7;
  color: #333;
}

/* 对话中的图片 */
.message-image {
  margin: 8px 0;
  max-width: 400px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}
.message-image img {
  width: 100%;
  height: auto;
  display: block;
}

/* Markdown 样式 */
.message-content :deep(p) { margin-bottom: 10px; }
.message-content :deep(p:last-child) { margin-bottom: 0; }
.message-content :deep(ul), .message-content :deep(ol) { padding-left: 20px; margin-bottom: 10px; }
.message-content :deep(li) { margin-bottom: 4px; }
.message-content :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #d63384;
}
.message-content :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.5;
}
.message-content :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
}
.message-content :deep(blockquote) {
  border-left: 3px solid #1a73e8;
  padding-left: 12px;
  color: #666;
  margin: 10px 0;
}
.message-content :deep(a) { color: #1a73e8; text-decoration: none; }
.message-content :deep(a:hover) { text-decoration: underline; }
.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}
.message-content :deep(th), .message-content :deep(td) {
  border: 1px solid #e0e0e0;
  padding: 8px 12px;
  text-align: left;
}
.message-content :deep(th) { background: #f5f5f5; }

/* 操作按钮 */
.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.15s;
}

.assistant-row:hover .message-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  transition: all 0.15s;
}

.action-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.action-btn.excel-btn:hover {
  background: #e8f5e9;
  color: #2e7d32;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ===== 输入区域 ===== */
.input-area {
  padding: 12px 24px 24px;
}

.input-container {
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 8px 8px 8px 12px;
  transition: box-shadow 0.2s, border-color 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.input-wrapper:focus-within {
  border-color: #1a73e8;
  box-shadow: 0 2px 12px rgba(26,115,232,0.12);
}

/* 模型选择 */
.model-select {
  padding: 5px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 12px;
  font-family: inherit;
  color: #333;
  background: #fafafa;
  cursor: pointer;
  outline: none;
  flex-shrink: 0;
  max-width: 200px;
}
.model-select:hover { border-color: #ccc; }
.model-select:focus { border-color: #1a73e8; }
.model-select:disabled { opacity: 0.5; cursor: not-allowed; }

/* 模式切换按钮（原始样式） */
.mode-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #999;
  transition: all 0.15s;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.mode-toggle:hover {
  background: #f5f5f5;
  border-color: #d0d0d0;
}

.mode-toggle.excel-toggle.active {
  background: #e8f5e9;
  border-color: #4caf50;
  color: #2e7d32;
}

.mode-toggle.search-toggle.active {
  background: #e3f2fd;
  border-color: #1a73e8;
  color: #1a73e8;
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  padding: 6px 0;
  color: #1a1a1a;
  font-size: 15px;
  font-family: inherit;
  resize: none;
  line-height: 1.5;
  max-height: 200px;
  min-width: 120px;
}

/* 图片预览 */
.image-preview {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #1a73e8;
  cursor: pointer;
  flex-shrink: 0;
  margin-bottom: 4px;
}
.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.image-remove {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  background: #ff4444;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  line-height: 1;
}
</style>
