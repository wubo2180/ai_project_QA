<template>
  <div class="profile-view">
    <div class="profile-card">
      <div class="profile-avatar">
        <span class="avatar-text">{{ user ? user.username.charAt(0).toUpperCase() : '?' }}</span>
      </div>
      <h2 class="profile-name">{{ user ? user.username : '未登录' }}</h2>
      <p class="profile-desc">基于大语言模型的智能问答系统</p>

      <div class="profile-stats">
        <div class="stat-item">
          <span class="stat-number">{{ stats.conversations }}</span>
          <span class="stat-label">对话数</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ stats.messages }}</span>
          <span class="stat-label">消息数</span>
        </div>
      </div>

      <div class="profile-info">
        <div class="info-row">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ user ? user.username : '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ user ? formatDate(user.date_joined) : '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">系统版本</span>
          <span class="info-value">v1.0.0</span>
        </div>
        <div class="info-row">
          <span class="info-label">Excel 导出</span>
          <span class="info-value status-ok">已支持</span>
        </div>
        <div class="info-row">
          <span class="info-label">网页搜索</span>
          <span class="info-value status-ok">已支持</span>
        </div>
      </div>

      <div class="profile-actions">
        <button class="back-btn" @click="$emit('back')">← 返回对话</button>
        <button v-if="user" class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const emit = defineEmits(["back", "logout"]);
const props = defineProps({ user: { type: Object, default: null } });
const stats = ref({ conversations: 0, messages: 0 });

onMounted(async () => {
  try {
    const res = await axios.get("/api/conversations/");
    const convs = res.data;
    const totalMessages = convs.reduce((sum, c) => sum + (c.message_count || 0), 0);
    stats.value = { conversations: convs.length, messages: totalMessages };
  } catch { /* ignore */ }
});

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("zh-CN");
}

async function handleLogout() {
  try {
    await axios.post("/api/auth/logout/");
    emit("logout");
  } catch { /* ignore */ }
}
</script>

<style scoped>
.profile-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #ffffff;
  padding: 20px;
}

.profile-card {
  max-width: 420px;
  width: 100%;
  text-align: center;
}

.profile-avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.avatar-text {
  font-size: 32px;
  color: white;
  font-weight: 700;
}

.profile-name {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.profile-desc {
  font-size: 14px;
  color: #999;
  margin-bottom: 28px;
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 28px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #1a73e8;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.profile-info {
  background: #f7f7f8;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
  text-align: left;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.info-row:last-child { border-bottom: none; }

.info-label { font-size: 14px; color: #666; }
.info-value { font-size: 14px; color: #1a1a1a; font-weight: 500; }
.status-ok { color: #2e7d32; }

.profile-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.back-btn {
  padding: 10px 24px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.back-btn:hover { opacity: 0.9; }

.logout-btn {
  padding: 10px 24px;
  background: #ffffff;
  color: #dc2626;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.logout-btn:hover { background: #fef2f2; }
</style>
