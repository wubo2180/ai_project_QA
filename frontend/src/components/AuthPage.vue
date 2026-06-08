<template>
  <div class="auth-view">
    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <div class="auth-avatar">AI</div>
        </div>
        <h2>{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
        <p class="auth-sub">{{ isLogin ? '登录以继续使用 AI 智能问答' : '注册一个新账号开始对话' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
            autocomplete="current-password"
          />
        </div>
        <div v-if="!isLogin" class="form-group">
          <label>确认密码</label>
          <input
            v-model="form.password2"
            type="password"
            placeholder="请再次输入密码"
            required
            autocomplete="new-password"
          />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="submit-btn" :disabled="submitting">
          {{ submitting ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <div class="auth-switch">
        <span v-if="isLogin">还没有账号？</span>
        <span v-else>已有账号？</span>
        <button class="switch-btn" @click="isLogin = !isLogin; errorMsg = ''">
          {{ isLogin ? '立即注册' : '立即登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import axios from "axios";

const emit = defineEmits(["login-success"]);

const isLogin = ref(true);
const submitting = ref(false);
const errorMsg = ref("");
const form = reactive({ username: "", password: "", password2: "" });

async function handleSubmit() {
  errorMsg.value = "";
  const { username, password, password2 } = form;

  if (!username.trim() || !password.trim()) {
    errorMsg.value = "请填写所有字段";
    return;
  }

  submitting.value = true;
  try {
    const endpoint = isLogin.value ? "/api/auth/login/" : "/api/auth/register/";
    const payload = isLogin.value
      ? { username: username.trim(), password }
      : { username: username.trim(), password, password2 };

    const res = await axios.post(endpoint, payload);
    emit("login-success", res.data.user);
  } catch (err) {
    errorMsg.value = err.response?.data?.error || "操作失败，请重试";
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.auth-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #ffffff;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 32px;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  margin-bottom: 16px;
}

.auth-avatar {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 700;
  margin: 0 auto;
}

.auth-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 6px;
}

.auth-sub {
  font-size: 14px;
  color: #999;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  color: #1a1a1a;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: #1a73e8;
}

.form-group input::placeholder {
  color: #bbb;
}

.error-msg {
  background: #fef2f2;
  color: #dc2626;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.submit-btn:hover { opacity: 0.9; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.auth-switch {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #999;
}

.switch-btn {
  background: none;
  border: none;
  color: #1a73e8;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0 4px;
}

.switch-btn:hover { text-decoration: underline; }
</style>
