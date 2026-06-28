<template>
  <div class="chat-view">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-content">
        <h1>知识库问答</h1>
        <p>基于上传的文档进行智能问答，支持流式输出</p>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0 && !loading" class="welcome-state">
        <div class="welcome-card">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12 6.48 2 12 2z"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9"/>
              <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
          </div>
          <h2>知识库智能问答</h2>
          <p>选择知识库后输入问题，系统将基于文档内容生成回答</p>
          <div class="welcome-tips">
            <div class="tip-item">
              <span class="tip-icon">💡</span>
              <span>支持多知识库同时查询</span>
            </div>
            <div class="tip-item">
              <span class="tip-icon">📊</span>
              <span>可调节相关度阈值过滤结果</span>
            </div>
            <div class="tip-item">
              <span class="tip-icon">⚡</span>
              <span>支持流式实时输出</span>
            </div>
          </div>
        </div>
      </div>
      <div v-for="(msg, index) in messages" :key="index" 
           :class="['message', msg.role]">
        <div class="message-avatar">
          <svg v-if="msg.role === 'user'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="10" rx="2"/>
            <circle cx="12" cy="5" r="2"/>
            <path d="M12 7v4"/>
            <line x1="8" y1="16" x2="8" y2="16"/>
            <line x1="16" y1="16" x2="16" y2="16"/>
          </svg>
        </div>
        <div class="message-content">
          <p v-if="msg.role === 'user'">{{ msg.content }}</p>
          <div v-else class="assistant-body" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>
      
      <!-- 加载提示 -->
      <div v-if="loading" class="message assistant">
        <div class="message-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="10" rx="2"/>
            <circle cx="12" cy="5" r="2"/>
            <path d="M12 7v4"/>
            <line x1="8" y1="16" x2="8" y2="16"/>
            <line x1="16" y1="16" x2="16" y2="16"/>
          </svg>
        </div>
        <div class="message-content thinking">
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 引用来源面板 -->
    <div v-if="sources.length > 0" class="sources-panel">
      <div class="sources-header" @click="sourcesExpanded = !sourcesExpanded">
        <h3>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          引用来源 ({{ sources.length }})
        </h3>
        <span class="expand-icon">{{ sourcesExpanded ? '▾' : '▸' }}</span>
      </div>
      <div v-show="sourcesExpanded" class="sources-content">
        <div v-for="(source, idx) in sources" :key="idx" class="source-item" @click="previewSource(source)">
          <div class="source-header">
            <span class="source-title">{{ source.source }}</span>
            <div class="source-badges">
              <span v-if="source.page" class="page-badge">P{{ source.page }}</span>
              <span :class="['score-badge', getScoreClass(source.score)]">{{ (source.score * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <p class="source-text">{{ truncateText(source.snippet, 150) }}</p>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <!-- 工具栏 -->
      <div class="toolbar">
        <button class="toolbar-btn" @click="showCollectionModal = true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          <span>知识库</span>
          <span class="toolbar-badge">{{ selectedCollections.length || 0 }}</span>
        </button>
        <div class="toolbar-divider"></div>
        <label class="toolbar-toggle">
          <input type="checkbox" v-model="useStream">
          <span>流式</span>
        </label>
        <div class="score-threshold-mini">
          <span>相关度≥{{ scoreThreshold }}%</span>
          <input type="range" v-model.number="scoreThreshold" min="0" max="100" step="5" class="mini-slider">
        </div>
      </div>

      <!-- 输入框 -->
      <form @submit.prevent="sendMessage" class="input-form">
        <input 
          v-model="question" 
          type="text" 
          placeholder="输入你的问题..." 
          :disabled="loading && !useStream"
          @keyup.enter="sendMessage"
        />
        <button 
          type="button"
          v-if="loading && useStream"
          @click="stopGeneration"
          class="stop-btn"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
          停止
        </button>
        <button 
          v-else
          type="submit" 
          class="send-btn"
          :disabled="!question.trim() || loading"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          发送
        </button>
      </form>
    </div>

    <!-- 知识库选择模态框 -->
    <div v-if="showCollectionModal" class="modal-overlay" @click="showCollectionModal = false">
      <div class="collection-modal" @click.stop>
        <div class="collection-modal-header">
          <div class="cmh-left">
            <h3>选择知识库</h3>
            <span class="cmh-count">已选 {{ selectedCollections.length }} / {{ collections.length }}</span>
          </div>
          <div class="cmh-actions">
            <button class="cmh-select-all-btn" @click="toggleSelectAllInModal">
              {{ selectedCollections.length === collections.length ? '取消全选' : '全选' }}
            </button>
            <button class="close-btn" @click="showCollectionModal = false">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="collection-modal-body">
          <div v-if="collections.length === 0" class="cm-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              <line x1="9" y1="14" x2="15" y2="14"/>
            </svg>
            <p>暂无知识库</p>
            <span>请先在「文档管理」中上传文档</span>
          </div>
          <div v-else class="cm-grid">
            <div 
              v-for="col in collections" :key="col.name" 
              :class="['cm-card', { selected: selectedCollections.includes(col.name) }]"
              @click="toggleCollection(col.name)"
            >
              <div class="cm-card-check">
                <svg v-if="selectedCollections.includes(col.name)" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <div class="cm-card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <div class="cm-card-name">{{ col.name }}</div>
              <div class="cm-card-meta">
                <span>{{ col.document_count }} 篇文档</span>
                <span>{{ col.chunk_count }} 分块</span>
              </div>
            </div>
          </div>
        </div>
        <div class="collection-modal-footer">
          <button class="cm-confirm-btn" @click="showCollectionModal = false">确认 ({{ selectedCollections.length }})</button>
        </div>
      </div>
    </div>

    <!-- 预览模态框 -->
    <div v-if="showPreview" class="modal-overlay" @click="closePreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ previewData?.source || '未知来源' }}</h3>
          <button @click="closePreview" class="close-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="previewData?.page" class="meta-info">
            <span>页码: {{ previewData.page }}</span>
            <span v-if="previewData?.file_type">类型: {{ previewData.file_type }}</span>
            <span>相关度: {{ (previewData.score * 100).toFixed(2) }}%</span>
          </div>
          <pre class="snippet">{{ previewData?.snippet || '无内容' }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'

// 状态
const question = ref('')
const messages = ref([])
const sources = ref([])
const loading = ref(false)
const useStream = ref(true)
const collections = ref([])
const selectedCollections = ref([])
const showPreview = ref(false)
const previewData = ref(null)
const messagesContainer = ref(null)
const scoreThreshold = ref(0)
const showCollectionModal = ref(false)

// 引用来源折叠状态
const sourcesExpanded = ref(false)

// 流式中断控制器
let abortController = null

// 加载知识库列表
async function loadCollections() {
  try {
    const res = await axios.get('/api/documents/collections')
    collections.value = res.data.collections || []
    selectedCollections.value = collections.value.map(c => c.name)
  } catch (err) {
    console.error('加载知识库失败:', err)
  }
}

// 切换全选
function toggleSelectAll(e) {
  if (e.target.checked) {
    selectedCollections.value = collections.value.map(c => c.name)
  } else {
    selectedCollections.value = []
  }
}

// 模态框内全选/取消全选
function toggleSelectAllInModal() {
  if (selectedCollections.value.length === collections.value.length) {
    selectedCollections.value = []
  } else {
    selectedCollections.value = collections.value.map(c => c.name)
  }
}

// 切换单个知识库选中状态
function toggleCollection(name) {
  const idx = selectedCollections.value.indexOf(name)
  if (idx >= 0) {
    selectedCollections.value.splice(idx, 1)
  } else {
    selectedCollections.value.push(name)
  }
}

// 获取选中的知识库
function getSelectedCollections() {
  if (selectedCollections.value.length > 0) {
    return selectedCollections.value
  }
  return null
}

// 发送消息
async function sendMessage() {
  if (!question.value.trim() || loading.value) return
  
  const userQuestion = question.value
  question.value = ''
  
  messages.value.push({ role: 'user', content: userQuestion })
  sources.value = []
  loading.value = true
  
  await nextTick()
  scrollToBottom()
  
  try {
    if (useStream.value) {
      await sendStreamRequest(userQuestion)
    } else {
      await sendNormalRequest(userQuestion)
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      messages.value.push({ 
        role: 'assistant', 
        content: `错误: ${err.message}` 
      })
    }
  } finally {
    loading.value = false
    abortController = null
    await nextTick()
    scrollToBottom()
  }
}

// 停止生成
function stopGeneration() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  loading.value = false
}

// 流式请求
async function sendStreamRequest(question) {
  abortController = new AbortController()
  
  const selectedCols = getSelectedCollections()
  
  const requestBody = {
    question,
    top_k: 5,
    stream: true
  }
  
  if (selectedCols && selectedCols.length > 0) {
    requestBody.collections = selectedCols
  }
  
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
    signal: abortController.signal
  })
  
  if (!response.ok) {
    let errorBody = ''
    try {
      errorBody = await response.text()
    } catch (e) {}
    throw new Error(`HTTP ${response.status}: ${errorBody || '未知错误'}`)
  }
  
  messages.value.push({ role: 'assistant', content: '' })
  sources.value = []
  const lastMessageIndex = messages.value.length - 1
  
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const decoded = decoder.decode(value, { stream: true })
      buffer += decoded.replace(/\r\n/g, '\n')
      
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      
      for (const eventStr of events) {
        if (!eventStr.trim()) continue
        
        let eventType = ''
        let eventData = ''
        
        const lines = eventStr.split('\n')
        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            if (eventData === '') {
              eventData = line.slice(5)
            } else {
              eventData += '\n' + line.slice(5)
            }
          }
        }
        
        if (!eventType) continue
        
        let parsedData
        try {
          parsedData = JSON.parse(eventData)
        } catch {
          parsedData = eventData
        }
        
        if (eventType === 'sources') {
          if (Array.isArray(parsedData)) {
            if (scoreThreshold.value > 0) {
              sources.value = parsedData.filter(s => s.score * 100 >= scoreThreshold.value)
            } else {
              sources.value = parsedData
            }
          }
        } else if (eventType === 'chunk') {
          const chunkText = typeof parsedData === 'string' ? parsedData : String(parsedData)
          const currentContent = messages.value[lastMessageIndex].content
          messages.value.splice(lastMessageIndex, 1, {
            role: 'assistant',
            content: currentContent + chunkText
          })
          await nextTick()
          scrollToBottom()
        } else if (eventType === 'error') {
          const errorMessage = typeof parsedData === 'object' && parsedData.message 
            ? parsedData.message 
            : String(parsedData)
          throw new Error(errorMessage || '未知错误')
        } else if (eventType === 'done') {
          break
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// 非流式请求
async function sendNormalRequest(question) {
  const selectedCols = getSelectedCollections()
  
  const requestBody = {
    question,
    top_k: 5,
    stream: false
  }
  
  if (selectedCols && selectedCols.length > 0) {
    requestBody.collections = selectedCols
  }
  
  const res = await axios.post('/api/chat', requestBody)
  
  messages.value.push({ role: 'assistant', content: res.data.answer })
  
  const allSources = res.data.sources || []
  if (scoreThreshold.value > 0) {
    sources.value = allSources.filter(s => s.score * 100 >= scoreThreshold.value)
  } else {
    sources.value = allSources
  }
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 渲染Markdown
function renderMarkdown(text) {
  return marked(text)
}

// 截断文本
function truncateText(text, length) {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 获取分数等级样式
function getScoreClass(score) {
  if (score >= 0.8) return 'score-high'
  if (score >= 0.6) return 'score-mid'
  return 'score-low'
}

// 预览来源
function previewSource(source) {
  previewData.value = source
  showPreview.value = true
}

// 关闭预览
function closePreview() {
  showPreview.value = false
  previewData.value = null
}

onMounted(() => {
  loadCollections()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 头部 */
.chat-header {
  padding: 16px 28px;
  background: var(--bg-surface);
  backdrop-filter: var(--blur-md);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.header-content h1 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-content p {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

/* 消息列表 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

/* 欢迎状态 */
.welcome-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  animation: fadeIn 0.5s ease;
}

.welcome-card {
  text-align: center;
  background: var(--bg-surface);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  max-width: 480px;
  box-shadow: var(--shadow-lg);
}

.welcome-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 50%;
  color: white;
  box-shadow: 0 8px 24px var(--primary-glow);
}

.welcome-card h2 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.welcome-card > p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px;
}

.welcome-tips {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-hover);
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  transition: all var(--transition-normal);
}

.tip-item:hover {
  background: rgba(6, 182, 212, 0.08);
  border-color: rgba(6, 182, 212, 0.2);
  transform: translateX(4px);
}

.tip-icon {
  font-size: 16px;
}

/* 消息 */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  animation: slideUp 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.message.assistant .message-avatar {
  background: var(--bg-hover);
  border: 1px solid var(--border-normal);
  color: var(--text-secondary);
}

.message-content {
  max-width: 68%;
  padding: 14px 18px;
  line-height: 1.7;
  font-size: 14px;
}

.message.user .message-content {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
  box-shadow: 0 4px 16px var(--primary-glow);
}

.message.assistant .message-content {
  background: var(--bg-surface);
  backdrop-filter: var(--blur-md);
  color: var(--text-primary);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm);
  border: 1px solid var(--border-normal);
}

.message-content p {
  margin: 0;
}

/* Markdown 样式 */
.assistant-body {
  line-height: 1.8;
}

.assistant-body p {
  margin: 0 0 10px;
}

.assistant-body p:last-child {
  margin-bottom: 0;
}

.assistant-body code {
  background: rgba(6, 182, 212, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: var(--primary-light);
}

.assistant-body pre {
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-primary);
  padding: 16px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.6;
  border: 1px solid var(--border-subtle);
}

.assistant-body pre code {
  background: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}

.assistant-body ul,
.assistant-body ol {
  padding-left: 20px;
  margin: 8px 0;
}

.assistant-body li {
  margin-bottom: 4px;
}

.assistant-body blockquote {
  border-left: 3px solid var(--primary);
  margin: 12px 0;
  padding: 8px 16px;
  background: rgba(6, 182, 212, 0.06);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-secondary);
}

.assistant-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 13px;
}

.assistant-body th,
.assistant-body td {
  border: 1px solid var(--border-normal);
  padding: 8px 12px;
  text-align: left;
}

.assistant-body th {
  background: var(--bg-hover);
  font-weight: 600;
}

.assistant-body h1,
.assistant-body h2,
.assistant-body h3,
.assistant-body h4 {
  margin: 16px 0 8px;
  color: var(--text-primary);
}

.assistant-body h1 { font-size: 18px; }
.assistant-body h2 { font-size: 16px; }
.assistant-body h3 { font-size: 15px; }

.assistant-body a {
  color: var(--primary-light);
  text-decoration: none;
}

.assistant-body a:hover {
  color: var(--primary);
  text-decoration: underline;
}

.assistant-body hr {
  border: none;
  border-top: 1px solid var(--border-normal);
  margin: 16px 0;
}

/* 思考动画 */
.thinking-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 引用来源 */
.sources-panel {
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  backdrop-filter: var(--blur-md);
  max-height: 35vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 28px;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}

.sources-header:hover {
  background: var(--bg-hover);
}

.sources-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.expand-icon {
  color: var(--text-tertiary);
  font-size: 14px;
}

.sources-content {
  overflow-y: auto;
  padding: 8px 28px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  padding: 12px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
  background: var(--bg-hover);
}

.source-item:hover {
  border-color: rgba(6, 182, 212, 0.3);
  background: rgba(6, 182, 212, 0.06);
  transform: translateX(4px);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.source-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.source-badges {
  display: flex;
  gap: 6px;
}

.page-badge {
  background: rgba(6, 182, 212, 0.15);
  color: var(--primary-light);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.score-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.score-high {
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
}

.score-mid {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.score-low {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

.source-text {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.5;
}

/* 输入区域 */
.chat-input-area {
  padding: 14px 28px 18px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  backdrop-filter: var(--blur-md);
  flex-shrink: 0;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-md);
  background: var(--bg-hover);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all var(--transition-normal);
}

.toolbar-btn:hover {
  border-color: rgba(6, 182, 212, 0.3);
  background: rgba(6, 182, 212, 0.08);
  color: var(--primary-light);
}

.toolbar-badge {
  background: var(--primary);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--border-normal);
}

.toolbar-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.toolbar-toggle input[type="checkbox"] {
  accent-color: var(--primary);
}

.score-threshold-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.score-threshold-mini span {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.mini-slider {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border-normal);
  border-radius: 2px;
  outline: none;
}

.mini-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  box-shadow: 0 2px 8px var(--primary-glow);
}

/* 输入表单 */
.input-form {
  display: flex;
  gap: 10px;
}

.input-form input {
  flex: 1;
  padding: 12px 18px;
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-lg);
  font-size: 14px;
  outline: none;
  transition: all var(--transition-normal);
  background: var(--bg-hover);
  color: var(--text-primary);
}

.input-form input::placeholder {
  color: var(--text-muted);
}

.input-form input:focus {
  border-color: var(--primary);
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all var(--transition-normal);
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--primary-glow);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.stop-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--danger), #dc2626);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all var(--transition-normal);
  white-space: nowrap;
  animation: pulse 2s infinite;
}

.stop-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--blur-md);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: var(--bg-elevated);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-xl);
  max-width: 800px;
  max-height: 80vh;
  width: 90%;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.25s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: var(--bg-hover);
  border: 1px solid var(--border-normal);
  cursor: pointer;
  color: var(--text-tertiary);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--danger);
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
}

.meta-info {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.meta-info span {
  background: var(--bg-hover);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
}

.modal-body pre.snippet {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  background: var(--bg-hover);
  padding: 16px 20px;
  border-radius: var(--radius-md);
  border-left: 3px solid var(--primary);
  margin: 0;
}

/* 知识库选择模态框 */
.collection-modal {
  background: var(--bg-elevated);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-xl);
  max-width: 640px;
  width: 92%;
  max-height: 75vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.25s ease;
}

.collection-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.cmh-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.cmh-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.cmh-count {
  font-size: 13px;
  color: var(--text-tertiary);
}

.cmh-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cmh-select-all-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-sm);
  background: var(--bg-hover);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.cmh-select-all-btn:hover {
  border-color: rgba(6, 182, 212, 0.3);
  background: rgba(6, 182, 212, 0.08);
  color: var(--primary-light);
}

.collection-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.cm-empty {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-muted);
}

.cm-empty svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.cm-empty p {
  margin: 0 0 4px;
  font-size: 15px;
  color: var(--text-secondary);
}

.cm-empty span {
  font-size: 13px;
}

.cm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
}

.cm-card {
  position: relative;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 16px 14px 12px;
  cursor: pointer;
  transition: all var(--transition-normal);
  text-align: center;
  background: var(--bg-hover);
}

.cm-card:hover {
  border-color: rgba(6, 182, 212, 0.2);
  background: rgba(6, 182, 212, 0.06);
  transform: translateY(-2px);
}

.cm-card.selected {
  border-color: var(--primary);
  background: rgba(6, 182, 212, 0.1);
  box-shadow: 0 4px 16px var(--primary-glow);
}

.cm-card-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--border-normal);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
}

.cm-card.selected .cm-card-check {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.cm-card-icon {
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.cm-card.selected .cm-card-icon {
  color: var(--primary-light);
}

.cm-card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cm-card-meta {
  display: flex;
  justify-content: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.collection-modal-footer {
  padding: 14px 24px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: flex-end;
}

.cm-confirm-btn {
  padding: 10px 28px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.cm-confirm-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--primary-glow);
}
</style>
