<template>
  <div class="kb-view">
    <div class="kb-header">
      <div class="kb-title-row">
        <h2 class="kb-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          知识库管理
        </h2>
        <button class="back-btn" @click="$emit('back')">← 返回对话</button>
      </div>

      <div class="kb-meta" v-if="dataset">
        <span class="kb-name">{{ dataset.name }}</span>
        <span class="kb-stat">{{ dataset.document_count }} 个文档</span>
        <span class="kb-stat" v-if="dataset.word_count">{{ formatNumber(dataset.word_count) }} 字</span>
      </div>
    </div>

    <div class="kb-toolbar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索文件名..."
          @keydown.enter="loadFiles"
        />
      </div>
      <button class="refresh-btn" :disabled="loading" @click="loadFiles">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }">
          <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        刷新
      </button>
    </div>

    <div class="kb-body">
      <div v-if="loading" class="kb-state">
        <div class="spinner"></div>
        <p>正在加载知识库文件...</p>
      </div>

      <div v-else-if="error" class="kb-state error">
        <p>⚠️ {{ error }}</p>
        <button class="retry-btn" @click="loadFiles">重试</button>
      </div>

      <div v-else-if="files.length === 0" class="kb-state">
        <p>📭 暂无文件</p>
      </div>

      <table v-else class="kb-table">
        <thead>
          <tr>
            <th class="col-idx">#</th>
            <th class="col-name">文件名</th>
            <th class="col-type">类型</th>
            <th class="col-size">大小</th>
            <th class="col-time">上传时间</th>
            <th class="col-status">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(file, idx) in files"
            :key="file.id"
            class="kb-row"
            @click="openDetail(file)"
          >
            <td class="col-idx">{{ idx + 1 }}</td>
            <td class="col-name">
              <span class="file-icon">{{ fileEmoji(file.extension) }}</span>
              <span class="file-name" :title="file.name">{{ file.name }}</span>
            </td>
            <td class="col-type">{{ (file.extension || '-').toUpperCase() }}</td>
            <td class="col-size">{{ formatSize(file.size) }}</td>
            <td class="col-time">{{ formatDateTime(file.created_at) }}</td>
            <td class="col-status">
              <span class="status-badge" :class="statusClass(file.indexing_status)">
                {{ statusLabel(file.indexing_status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 文档详情弹窗 -->
    <div v-if="detailFile" class="kb-modal-overlay" @click.self="detailFile = null">
      <div class="kb-modal">
        <div class="kb-modal-header">
          <h3 class="kb-modal-title">
            <span class="file-icon">{{ fileEmoji(detailFile.extension) }}</span>
            <span :title="detailFile.name">{{ detailFile.name }}</span>
          </h3>
          <button class="kb-modal-close" @click="detailFile = null">✕</button>
        </div>
        <div class="kb-modal-body">
          <div class="detail-row">
            <span class="detail-label">文档 ID</span>
            <span class="detail-value mono">{{ detailFile.id }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">文件类型</span>
            <span class="detail-value">{{ (detailFile.extension || '-').toUpperCase() }}<template v-if="detailFile.mime_type"> ({{ detailFile.mime_type }})</template></span>
          </div>
          <div class="detail-row">
            <span class="detail-label">文件大小</span>
            <span class="detail-value">{{ formatSize(detailFile.size) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">字数</span>
            <span class="detail-value">{{ formatNumber(detailFile.word_count) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Token 数</span>
            <span class="detail-value">{{ formatNumber(detailFile.tokens) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">命中次数</span>
            <span class="detail-value">{{ formatNumber(detailFile.hit_count) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">索引状态</span>
            <span class="detail-value">
              <span class="status-badge" :class="statusClass(detailFile.indexing_status)">
                {{ statusLabel(detailFile.indexing_status) }}
              </span>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">是否启用</span>
            <span class="detail-value">{{ detailFile.enabled ? '已启用' : '已禁用' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">上传来源</span>
            <span class="detail-value">{{ detailFile.created_from || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">上传时间</span>
            <span class="detail-value">{{ formatDateTime(detailFile.created_at) }}</span>
          </div>
          <div class="detail-row" v-if="detailFile.error">
            <span class="detail-label">错误信息</span>
            <span class="detail-value error-text">{{ detailFile.error }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

defineEmits(["back"]);

const loading = ref(false);
const error = ref("");
const dataset = ref(null);
const files = ref([]);
const keyword = ref("");
const detailFile = ref(null);

onMounted(loadFiles);

function openDetail(file) {
  detailFile.value = file;
}

async function loadFiles() {
  loading.value = true;
  error.value = "";
  try {
    const params = {};
    if (keyword.value.trim()) params.keyword = keyword.value.trim();
    const res = await axios.get("/api/knowledge-base/", { params });
    dataset.value = res.data.dataset;
    files.value = res.data.files || [];
  } catch (e) {
    error.value = e.response?.data?.error || "加载失败，请检查网络连接";
    files.value = [];
  } finally {
    loading.value = false;
  }
}

function formatSize(bytes) {
  if (!bytes) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatNumber(n) {
  return (n || 0).toLocaleString("zh-CN");
}

function formatDateTime(ts) {
  if (!ts) return "-";
  // Dify created_at 为秒级 unix 时间戳
  const d = new Date(ts * 1000);
  if (isNaN(d.getTime())) return "-";
  const pad = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fileEmoji(ext) {
  const map = {
    pdf: "📕", doc: "📘", docx: "📘", txt: "📄", md: "📝",
    csv: "📊", xlsx: "📊", xls: "📊", ppt: "📙", pptx: "📙",
    html: "🌐", json: "🧩",
  };
  return map[(ext || "").toLowerCase()] || "📄";
}

const STATUS_MAP = {
  completed: { label: "已完成", cls: "ok" },
  indexing: { label: "索引中", cls: "pending" },
  parsing: { label: "解析中", cls: "pending" },
  splitting: { label: "分段中", cls: "pending" },
  waiting: { label: "等待中", cls: "pending" },
  error: { label: "失败", cls: "fail" },
  paused: { label: "已暂停", cls: "fail" },
};

function statusLabel(s) {
  return STATUS_MAP[s]?.label || s || "-";
}
function statusClass(s) {
  return STATUS_MAP[s]?.cls || "pending";
}
</script>

<style scoped>
.kb-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
  padding: 24px 32px;
  box-sizing: border-box;
}

.kb-header {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.kb-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kb-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.kb-title svg { color: #1a73e8; }

.back-btn {
  padding: 8px 18px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.15s;
}
.back-btn:hover { opacity: 0.9; }

.kb-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

.kb-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a73e8;
  background: #e8f0fe;
  padding: 4px 12px;
  border-radius: 6px;
}

.kb-stat { font-size: 13px; color: #999; }

.kb-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 360px;
  padding: 8px 12px;
  background: #f7f7f8;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}
.search-box svg { color: #999; flex-shrink: 0; }
.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #1a1a1a;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #ffffff;
  color: #1a73e8;
  border: 1px solid #1a73e8;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.refresh-btn:hover:not(:disabled) { background: #e8f0fe; }
.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.kb-body {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 12px;
}

.kb-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  color: #999;
  font-size: 14px;
}
.kb-state.error p { color: #dc2626; }

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e8f0fe;
  border-top-color: #1a73e8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.retry-btn, .kb-state .retry-btn {
  padding: 8px 20px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.kb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  table-layout: fixed;
}

.kb-table thead th {
  position: sticky;
  top: 0;
  background: #f7f7f8;
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  color: #666;
  border-bottom: 1px solid #eee;
  z-index: 1;
}

.kb-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  color: #1a1a1a;
}

.kb-table tbody tr:hover { background: #fafbff; }

.col-idx { width: 48px; color: #bbb; }
.col-type { width: 72px; }
.col-size { width: 92px; color: #666; }
.col-time { width: 150px; color: #666; }
.col-status { width: 100px; }

.kb-row { cursor: pointer; }

td.col-name {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.file-icon { margin-right: 8px; }
.file-name { vertical-align: middle; }

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.ok { background: #e8f5e9; color: #2e7d32; }
.status-badge.pending { background: #fff8e1; color: #f57c00; }
.status-badge.fail { background: #fef2f2; color: #dc2626; }

/* 文档详情弹窗 */
.kb-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.kb-modal {
  background: #ffffff;
  border-radius: 14px;
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.kb-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid #eee;
}

.kb-modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  overflow: hidden;
}
.kb-modal-title span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-modal-close {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  background: #f2f2f2;
  border-radius: 6px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.kb-modal-close:hover { background: #e5e5e5; }

.kb-modal-body {
  padding: 8px 20px 20px;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 11px 0;
  border-bottom: 1px solid #f2f2f2;
}
.detail-row:last-child { border-bottom: none; }

.detail-label {
  font-size: 13px;
  color: #888;
  flex-shrink: 0;
}
.detail-value {
  font-size: 13px;
  color: #1a1a1a;
  text-align: right;
  word-break: break-all;
}
.detail-value.mono {
  font-family: "Consolas", "Monaco", monospace;
  font-size: 12px;
  color: #555;
}
.error-text { color: #dc2626; }
</style>
