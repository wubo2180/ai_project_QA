<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="newChat">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>新建对话</span>
        </button>
      </div>

      <div class="history-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="history-item"
          :class="{ active: conv.id === activeConvId }"
          @click="switchConversation(conv)"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span class="history-title">{{ conv.title }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="sidebar-footer-item user-item" @click="showProfile = true">
          <div class="user-avatar">U</div>
          <span>个人中心</span>
        </div>
      </div>

      <button
        class="collapse-btn"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
    </aside>

    <!-- 主区域 -->
    <div class="main-area">
      <ProfilePage v-if="showProfile" @back="showProfile = false" />
      <ChatBox
        v-else
        :messages="currentMessages"
        :loading="loading"
        @send="handleSend"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import axios from "axios";
import ChatBox from "./components/ChatBox.vue";
import ProfilePage from "./components/ProfilePage.vue";

const sidebarCollapsed = ref(false);
const showProfile = ref(false);
const conversations = ref([]);
const activeConvId = ref(null);
const localConv = ref(null); // 当前本地未保存的对话
const loading = ref(false);

const currentMessages = computed(() => {
  if (localConv.value) return localConv.value.messages;
  const conv = conversations.value.find((c) => c.id === activeConvId.value);
  return conv?.messages || [];
});

// 加载历史列表
onMounted(async () => {
  try {
    const res = await axios.get("/api/conversations/");
    conversations.value = res.data;
  } catch { /* ignore */ }
});

function newChat() {
  showProfile.value = false;
  localConv.value = { id: null, title: "新对话", messages: [] };
  activeConvId.value = null;
}

async function switchConversation(conv) {
  showProfile.value = false;
  localConv.value = null;
  activeConvId.value = conv.id;
  // 如果还没有消息，加载详情
  if (!conv.messages || conv.messages.length === 0) {
    try {
      const res = await axios.get(`/api/conversations/${conv.id}/`);
      conv.messages = res.data.messages;
    } catch { conv.messages = []; }
  }
}

async function saveMessage(convId, msg) {
  try {
    await axios.post(`/api/conversations/${convId}/messages/`, msg);
  } catch { /* ignore */ }
}

async function handleSend(payload) {
  const text = typeof payload === "string" ? payload : payload.text;
  const excelMode = typeof payload === "string" ? false : payload.excelMode;
  const webSearch = typeof payload === "string" ? false : payload.webSearch;

  let conv = localConv.value || conversations.value.find((c) => c.id === activeConvId.value);
  if (!conv) {
    localConv.value = { id: null, title: "新对话", messages: [] };
    conv = localConv.value;
    activeConvId.value = null;
  }

  conv.messages.push({ role: "user", content: text });
  if (conv.title === "新对话") {
    conv.title = text.length > 20 ? text.slice(0, 20) + "..." : text;
  }
  loading.value = true;

  // 流式消息占位
  const assistantMsg = { role: "assistant", content: "", streaming: true, excelMode };
  conv.messages.push(assistantMsg);

  try {
    const history = conv.messages
      .filter((m) => m.role !== "system" && !m.streaming)
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }));

    if (excelMode) {
      history.unshift({
        role: "system",
        content: "请尽量使用 Markdown 表格格式整理和呈现数据，确保每个表格都有明确的表头行和分隔行（如 |---|），以便后续导出为 Excel。",
      });
    }

    const response = await fetch("/api/chat-stream/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history, web_search: webSearch }),
    });

    if (!response.ok || !response.body) throw new Error("Stream not available");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "chunk") {
              assistantMsg.content += data.content;
              conv.messages = [...conv.messages];
            } else if (data.type === "done") {
              assistantMsg.content = data.content;
              assistantMsg.streaming = false;
              conv.messages = [...conv.messages];

              // ---- 保存到数据库 ----
              // 如果是本地新对话，先创建 Conversation
              if (!conv.id && localConv.value) {
                try {
                  const createRes = await axios.post("/api/conversations/", { title: conv.title });
                  conv.id = createRes.data.id;
                  conversations.value.unshift(createRes.data);
                  activeConvId.value = conv.id;
                  localConv.value = null;
                } catch { /* ignore */ }
              }
              // 保存用户消息
              if (conv.id) {
                await saveMessage(conv.id, { role: "user", content: text });
                await saveMessage(conv.id, { role: "assistant", content: data.content, excel_mode: excelMode });
              }
            } else if (data.type === "error") {
              assistantMsg.content = data.content;
              assistantMsg.streaming = false;
              conv.messages = [...conv.messages];
            }
          } catch { /* ignore */ }
        }
      }
    }
  } catch (err) {
    assistantMsg.content = "抱歉，服务暂时不可用，请稍后重试。";
    assistantMsg.streaming = false;
    conv.messages = [...conv.messages];
  } finally {
    loading.value = false;
    if (assistantMsg.streaming) {
      assistantMsg.streaming = false;
      conv.messages = [...conv.messages];
    }
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background: #f5f5f5;
  color: #1a1a1a;
  overflow: hidden;
}

.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #ffffff;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.2s, min-width 0.2s;
}

.sidebar.collapsed { width: 0; min-width: 0; overflow: hidden; border-right: none; }

.sidebar-header { padding: 16px; border-bottom: 1px solid #f0f0f0; }

.new-chat-btn {
  width: 100%; padding: 10px; display: flex; align-items: center; justify-content: center; gap: 6px;
  background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 14px; color: #333; cursor: pointer; transition: all 0.15s;
}
.new-chat-btn:hover { background: #f5f5f5; border-color: #d0d0d0; }

.history-list { flex: 1; overflow-y: auto; padding: 8px; }
.history-list::-webkit-scrollbar { width: 4px; }
.history-list::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

.history-item {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 8px;
  font-size: 13px; color: #666; cursor: pointer; transition: all 0.15s; margin-bottom: 2px;
}
.history-item:hover { background: #f0f0f0; }
.history-item.active { background: #e8f0fe; color: #1a73e8; }
.history-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer { border-top: 1px solid #f0f0f0; padding: 8px 12px; }

.sidebar-footer-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #999; cursor: pointer; padding: 6px 4px; border-radius: 6px; transition: background 0.15s; }
.sidebar-footer-item:hover { background: #f0f0f0; color: #333; }

.user-avatar {
  width: 28px; height: 28px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; font-weight: 700;
}

.collapse-btn {
  position: absolute; right: -28px; top: 50%; transform: translateY(-50%);
  width: 28px; height: 48px; background: #ffffff; border: 1px solid #e5e5e5; border-left: none;
  border-radius: 0 8px 8px 0; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #999; z-index: 10;
}
.collapse-btn:hover { color: #333; }

/* ===== 主区域 ===== */
.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
</style>
