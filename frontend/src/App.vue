<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="newChat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>新建对话</span>
        </button>
      </div>

      <!-- 登录用户：显示历史对话列表 -->
      <div class="history-list" v-if="user">
        <div
          v-for="conv in conversations"
          :key="conv.id || conv._tempId"
          class="history-item"
          :class="{ active: conv.id === activeConvId || (localConv && localConv === conv) }"
          @click="switchConversation(conv)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <template v-if="editingConvId !== conv.id">
            <span
              class="history-title"
              @dblclick="startRename(conv)"
              :title="conv.title"
            >{{ conv.title }}</span>
          </template>
          <input
            v-else
            v-model="renameText"
            class="rename-input"
            ref="renameInputRef"
            @blur="confirmRename(conv)"
            @keydown.enter="confirmRename(conv)"
            @keydown.escape="cancelRename"
            @click.stop
          />
        </div>
      </div>

      <!-- 游客模式：显示登录提示 -->
      <div class="guest-hint" v-else>
        <div class="guest-icon">🗂️</div>
        <p>登录后可查看历史对话</p>
        <button class="guest-login-btn" @click="openUserPage">立即登录</button>
      </div>

      <div class="sidebar-footer">
        <div class="sidebar-footer-item" @click="openUserPage">
          <div class="user-avatar">{{ user ? user.username.charAt(0).toUpperCase() : '?' }}</div>
          <span>{{ user ? user.username : '点击登录' }}</span>
        </div>
      </div>
    </aside>

    <!-- 折叠按钮 -->
    <button class="collapse-btn" :class="{ collapsed: sidebarCollapsed }" @click="sidebarCollapsed = !sidebarCollapsed">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline :points="sidebarCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'" />
      </svg>
    </button>

    <!-- 主区域 -->
    <div class="main-area">
      <AuthPage v-if="showAuth" @login-success="onLoginSuccess" />
      <ProfilePage
        v-else-if="showProfile"
        :user="user"
        @back="showProfile = false"
        @logout="onLogout"
      />
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
import { ref, computed, onMounted, nextTick } from "vue";
import axios from "axios";
import ChatBox from "./components/ChatBox.vue";
import ProfilePage from "./components/ProfilePage.vue";
import AuthPage from "./components/AuthPage.vue";

const sidebarCollapsed = ref(false);
const showProfile = ref(false);
const showAuth = ref(false);
const user = ref(null);
const conversations = ref([]);
const activeConvId = ref(null);
const localConv = ref(null);
const loading = ref(false);
const editingConvId = ref(null);
const renameText = ref("");
const renameInputRef = ref(null);
const streamVersion = ref(0); // 每次收到 chunk 自增，触发 ChatBox 重新渲染

const currentMessages = computed(() => {
  // 依赖 streamVersion，确保每次 chunk 后重新计算并生成新数组引用
  void streamVersion.value;
  if (localConv.value) return [...localConv.value.messages];
  const conv = conversations.value.find((c) => c.id === activeConvId.value);
  return conv?.messages ? [...conv.messages] : [];
});

onMounted(async () => {
  try {
    const userRes = await axios.get("/api/auth/me/");
    if (userRes.data.user) {
      user.value = userRes.data.user;
      await loadConversations();
    }
  } catch (e) {
    console.error("获取用户信息失败:", e);
  }
});

async function loadConversations() {
  try {
    const res = await axios.get("/api/conversations/");
    conversations.value = res.data;
    console.log("已加载对话列表:", conversations.value.length, "个对话");
  } catch (e) {
    console.error("加载对话列表失败:", e);
  }
}

// ---- 标题编辑 ----
function startRename(conv) {
  editingConvId.value = conv.id;
  renameText.value = conv.title;
  nextTick(() => {
    const el = renameInputRef.value;
    if (el) { el.focus(); el.select(); }
  });
}

async function confirmRename(conv) {
  const newTitle = renameText.value.trim();
  editingConvId.value = null;
  if (!newTitle || newTitle === conv.title) return;
  try {
    await axios.patch(`/api/conversations/${conv.id}/`, { title: newTitle });
    conv.title = newTitle;
  } catch (e) {
    console.error("重命名失败:", e);
  }
}

function cancelRename() {
  editingConvId.value = null;
}

// ---- 用户 ----
function openUserPage() {
  showProfile.value = true;
  showAuth.value = false;
  if (!user.value) {
    showProfile.value = false;
    showAuth.value = true;
  }
}

function onLoginSuccess(u) {
  user.value = u;
  showAuth.value = false;
  showProfile.value = false;
  loadConversations();
}

function onLogout() {
  user.value = null;
  showAuth.value = false;
  showProfile.value = false;
  conversations.value = [];
  activeConvId.value = null;
  localConv.value = null;
}

// ---- 对话管理 ----
function newChat() {
  showProfile.value = false;
  showAuth.value = false;
  // 创建一个临时对话对象，加入侧边栏
  const newConv = { id: null, _tempId: "new-" + Date.now(), title: "新对话", messages: [], _isNew: true };
  conversations.value.unshift(newConv);
  activeConvId.value = null;
  localConv.value = newConv;
}

async function switchConversation(conv) {
  showProfile.value = false;
  showAuth.value = false;
  localConv.value = null;
  activeConvId.value = conv.id;
  if (!conv.messages || conv.messages.length === 0) {
    try {
      const res = await axios.get(`/api/conversations/${conv.id}/`);
      conv.messages = res.data.messages;
    } catch (e) {
      console.error("加载对话消息失败:", e);
      conv.messages = [];
    }
  }
}

// ---- 消息发送与持久化 ----
async function handleSend(payload) {
  const text = typeof payload === "string" ? payload : payload.text;
  const excelMode = typeof payload === "string" ? false : payload.excelMode;
  const webSearch = typeof payload === "string" ? false : payload.webSearch;
  const model = payload.model || "deepseek";
  const imageData = payload.imageData || null;

  // 获取当前对话对象
  let conv = localConv.value;
  if (!conv) {
    conv = conversations.value.find((c) => c.id === activeConvId.value);
  }
  if (!conv) {
    // 理论上不会进来，兜底
    conv = { id: null, title: "新对话", messages: [], _isNew: true };
    conversations.value.unshift(conv);
  }

  // 确保 localConv 指向当前对话（保持响应式追踪）
  localConv.value = conv;
  activeConvId.value = null;

  // 添加用户消息
  const userMsg = { role: "user", content: text };
  if (imageData) userMsg.imageData = imageData;
  conv.messages.push(userMsg);
  loading.value = true;

  // ========== 先保存对话和用户消息到数据库 =========
  const isNewConversation = !conv.id;
  if (isNewConversation) {
    try {
      const createRes = await axios.post("/api/conversations/", {});
      conv.id = createRes.data.id;
      conv._isNew = false;
      console.log("对话已创建:", conv.id);
    } catch (e) {
      console.error("创建对话记录失败:", e);
      alert("创建对话失败，请检查网络连接");
      loading.value = false;
      return;
    }
  }

  // 保存用户消息
  try {
    const msgRes = await axios.post(`/api/conversations/${conv.id}/messages/`, {
      role: "user",
      content: text,
    });
    const lastMsg = conv.messages[conv.messages.length - 1];
    if (lastMsg) lastMsg._saved = true;

    // 后端自动生成了标题（用户的第一条消息），立即同步到侧边栏
    if (msgRes.data._conversation_title) {
      conv.title = msgRes.data._conversation_title;
      // 遍历侧边栏更新所有引用到此对话的标题（conv 和 sidebar item 是同一对象，确保 Vue 响应式）
      conversations.value.forEach(c => {
        if (c.id === conv.id) c.title = msgRes.data._conversation_title;
      });
    }
  } catch (e) {
    console.error("保存用户消息失败:", e);
  }

  // ========== 开始LLM流式请求 =========
  const assistantMsg = { role: "assistant", content: "", streaming: true, excelMode };
  conv.messages.push(assistantMsg);

  let streamFinished = false;

  try {
    const history = conv.messages
      .filter((m) => m.role !== "system" && m._saved)
      .map((m) => ({ role: m.role, content: m.content }));

    if (excelMode) {
      history.unshift({
        role: "system",
        content: "请尽量使用 Markdown 表格格式整理和呈现数据，每个表格必须有表头行和分隔行（如 |---|）。",
      });
    }

    const response = await fetch("/api/chat-stream/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history, web_search: webSearch, model, image_data: imageData }),
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
        if (!line.startsWith("data: ")) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === "chunk") {
            assistantMsg.content += data.content;
            streamVersion.value++; // 触发重渲染
          } else if (data.type === "done" || data.type === "error") {
            assistantMsg.content = data.content || assistantMsg.content;
            assistantMsg.streaming = false;
            streamFinished = true;

            // 出错或内容为空时，给出占位提示，且不保存空消息到后端
            if (!assistantMsg.content || !assistantMsg.content.trim()) {
              assistantMsg.content = "抱歉，未能获取到回复，请稍后重试或更换模型。";
              streamVersion.value++;
            } else {
              try {
                await axios.post(`/api/conversations/${conv.id}/messages/`, {
                  role: "assistant",
                  content: assistantMsg.content,
                  excel_mode: excelMode,
                });
                assistantMsg._saved = true;
                console.log("AI回复已保存");
                // 更新侧边栏中的消息列表（下次进入能看到消息）
                const item = conversations.value.find(c => c.id === conv.id);
                if (item) item.messages = conv.messages;
              } catch (e) {
                console.error("保存AI回复失败:", e);
              }
            }
          }
        } catch (e) {
          console.error("流式数据解析异常:", e);
        }
      }
    }
  } catch (err) {
    console.error("对话流异常:", err);
    if (!assistantMsg.content) {
      assistantMsg.content = "抱歉，服务暂时不可用，请稍后重试。";
    }
    assistantMsg.streaming = false;
    streamFinished = true;
  } finally {
    loading.value = false;
    if (assistantMsg.streaming) {
      assistantMsg.streaming = false;
      streamFinished = true;
    }

    // ========== 流结束后：迁移到侧边栏 =========
    if (localConv.value === conv) {
      localConv.value = null;
      activeConvId.value = conv.id;

      // 确保侧边栏有此对话并更新数据
      const existing = conversations.value.find(c => c.id === conv.id);
      if (existing) {
        existing.messages = conv.messages;
        existing.title = conv.title;
        existing.message_count = conv.messages.filter(m => m._saved).length;
      }
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
  background: #ffffff;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 260px;
  min-width: 260px;
  background: #ffffff;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  transition: width 0.2s, min-width 0.2s;
}

.sidebar.collapsed {
  width: 0;
  min-width: 0;
  border-right: none;
  overflow: hidden;
}

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
  position: relative;
}
.history-item:hover { background: #f0f0f0; }
.history-item.active {
  background: #e8f0fe; color: #1a73e8;
  padding-left: 16px;
}
/* 激活项的彩色竖条指示器 */
.history-item.active::before {
  content: "";
  position: absolute;
  left: 4px;
  top: 20%;
  height: 60%;
  width: 3px;
  background: #1a73e8;
  border-radius: 2px;
}

.history-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: default; }

/* 游客提示 */
.guest-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  color: #999;
  gap: 10px;
}
.guest-icon { font-size: 36px; opacity: 0.6; }
.guest-hint p { font-size: 13px; margin: 0; }
.guest-login-btn {
  margin-top: 4px;
  padding: 6px 20px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.guest-login-btn:hover { background: #1557b0; }

.rename-input {
  flex: 1;
  min-width: 0;
  padding: 2px 6px;
  border: 1px solid #1a73e8;
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
  color: #1a1a1a;
  outline: none;
  background: #fff;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.sidebar-footer:hover { background: #f5f5f5; }

.user-avatar {
  width: 32px;
  height: 32px;
  background: #1a73e8;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
}
/* 折叠按钮（在侧边栏外部） */
.collapse-btn {
  width: 28px;
  height: 48px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a73e8;
  flex-shrink: 0;
  align-self: center;
  transition: all 0.2s;
  margin-left: -1px;
  z-index: 10;
}

.collapse-btn:hover {
  color: #1557b0;
  background: #e8f0fe;
  border-color: #1a73e8;
}

.collapse-btn.collapsed {
  border-radius: 8px 0 0 8px;
  margin-left: 0;
  border-left: 1px solid #e5e5e5;
}

/* ===== 主区域 ===== */
.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
</style>
