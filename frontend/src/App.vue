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
import { ref } from 'vue'
import ChatView from './views/ChatView.vue'
import UploadView from './views/UploadView.vue'

const currentView = ref('chat')
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
  background: rgba(6, 182, 212, 0.1);
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

/* 底部 */
.sidebar-footer {
  padding: 16px 20px;
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
