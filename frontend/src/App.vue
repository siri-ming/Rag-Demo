<template>
  <div class="app-container">
    <!-- 侧边栏导航 -->
    <nav class="sidebar">
      <div class="logo">
        <div class="logo-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <div class="logo-text">
          <h2>RAG Demo</h2>
          <span class="logo-subtitle">知识库系统</span>
        </div>
      </div>
      
      <ul class="nav-links">
        <li :class="{ active: currentView === 'chat' }" @click="currentView = 'chat'">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </span>
          <span class="nav-label">智能问答</span>
          <span class="nav-indicator"></span>
        </li>
        <li :class="{ active: currentView === 'upload' }" @click="currentView = 'upload'">
          <span class="nav-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </span>
          <span class="nav-label">文档管理</span>
          <span class="nav-indicator"></span>
        </li>
      </ul>
      
      <!-- 主题切换 -->
      <div class="theme-section">
        <div class="theme-label">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          主题
        </div>
        <div class="theme-options">
          <button 
            v-for="t in themes" :key="t.id"
            :class="['theme-btn', { active: currentTheme === t.id }]"
            :title="t.name"
            @click="setTheme(t.id)"
          >
            <span class="theme-dot" :style="{ background: t.preview }"></span>
            <span class="theme-name">{{ t.name }}</span>
          </button>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="status-dot"></div>
        <span class="version-tag">v1.0.0</span>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <ChatView v-if="currentView === 'chat'" />
      <UploadView v-if="currentView === 'upload'" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatView from './views/ChatView.vue'
import UploadView from './views/UploadView.vue'

const currentView = ref('chat')

// 主题配置
const themes = [
  { id: 'dark', name: '暗色', preview: 'linear-gradient(135deg, #0ea5e9, #a78bfa)' },
  { id: 'light', name: '亮色', preview: 'linear-gradient(135deg, #0284c7, #7c3aed)' },
]

const currentTheme = ref('dark')

function setTheme(id) {
  currentTheme.value = id
  document.documentElement.setAttribute('data-theme', id)
  localStorage.setItem('rag-theme', id)
}

onMounted(() => {
  const saved = localStorage.getItem('rag-theme')
  if (saved && themes.some(t => t.id === saved)) {
    setTheme(saved)
  }
})
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: var(--bg-elevated);
  backdrop-filter: var(--blur-lg);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* Logo */
.logo {
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: var(--radius-md);
  color: white;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-text h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.logo-subtitle {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 导航 */
.nav-links {
  list-style: none;
  padding: 16px 12px;
  margin: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-links li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  position: relative;
  transition: all var(--transition-normal);
}

.nav-links li:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-links li.active {
  background: var(--bg-hover);
  color: var(--primary-light);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  transition: transform var(--transition-fast);
}

.nav-links li:hover .nav-icon {
  transform: scale(1.1);
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.nav-indicator {
  position: absolute;
  right: 12px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  opacity: 0;
  transform: scale(0);
  transition: all var(--transition-normal);
}

.nav-links li.active .nav-indicator {
  opacity: 1;
  transform: scale(1);
  box-shadow: 0 0 8px var(--primary-glow);
}

/* 主题切换 */
.theme-section {
  padding: 12px 16px;
  border-top: 1px solid var(--border-subtle);
}

.theme-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
}

.theme-options {
  display: flex;
  gap: 8px;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  transition: all var(--transition-normal);
  color: var(--text-tertiary);
}

.theme-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-normal);
  color: var(--text-secondary);
}

.theme-btn.active {
  border-color: var(--primary);
  background: var(--bg-hover);
  color: var(--text-primary);
  box-shadow: 0 0 0 1px var(--primary-glow);
}

.theme-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.theme-btn.active .theme-dot {
  border-color: var(--primary);
  box-shadow: 0 0 8px var(--primary-glow);
}

.theme-name {
  font-size: 12px;
  font-weight: 500;
}

/* 底部 */
.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
  animation: pulse 2s infinite;
}

.version-tag {
  font-size: 12px;
  color: var(--text-muted);
}

/* 主内容 */
.main-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-base);
  position: relative;
}
</style>
