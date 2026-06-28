<template>
  <div class="upload-view">
    <!-- 头部 -->
    <div class="upload-header">
      <h1>文档管理</h1>
      <p>上传文档到知识库，支持 PDF、Word、Excel、Markdown、图片等格式</p>
    </div>

    <!-- 上传区域 -->
    <div class="upload-section">
      <div 
        class="upload-zone" 
        :class="{ 'drag-over': isDragOver }"
        @dragover.prevent="isDragOver = true"
        @dragleave="isDragOver = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <div class="upload-icon">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <polyline points="9 15 12 12 15 15"/>
          </svg>
        </div>
        <p>拖拽文件到此处，或点击选择文件</p>
        <p class="upload-hint">
          支持格式: {{ supportedExtensions.join(', ') }}
        </p>
        <input 
          type="file" 
          ref="fileInputRef" 
          multiple 
          hidden
          @change="handleFileSelect"
        />
      </div>

      <!-- 上传选项 -->
      <div class="upload-options">
        <div class="option-group">
          <label>知识库名称:</label>
          <input 
            v-model="collectionName" 
            type="text" 
            placeholder="留空则使用文件名"
          />
        </div>
        
        <div class="option-group">
          <label>分块策略:</label>
          <select v-model="chunkStrategy">
            <option value="recursive">recursive</option>
            <option value="fixed_size">fixed_size</option>
            <option value="parent_child">parent_child</option>
          </select>
        </div>
        
        <div class="option-group">
          <label>分块大小:</label>
          <input 
            v-model.number="chunkSize" 
            type="number" 
            min="100" 
            max="5000"
            step="100"
            placeholder="500"
          />
        </div>
        
        <div class="option-group">
          <label>分块重叠:</label>
          <input 
            v-model.number="chunkOverlap" 
            type="number" 
            min="0" 
            max="500"
            step="10"
            placeholder="50"
          />
        </div>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadProgress.show" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress.percent + '%' }"></div>
      </div>
      <p>{{ uploadProgress.text }}</p>
    </div>

    <!-- 文档列表 -->
    <div class="doc-list-section">
      <div class="doc-list-header">
        <h2>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          已上传文档
        </h2>
        <button 
          v-if="documents.length > 0" 
          @click="clearAllDocuments" 
          class="btn-danger"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          清空知识库
        </button>
      </div>
      
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      <div v-else-if="documents.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="9" y1="14" x2="15" y2="14"/>
        </svg>
        <p>暂无文档，请先上传文件</p>
      </div>
      
      <div v-else class="doc-list">
        <div v-for="doc in documents" :key="doc.doc_id" class="doc-card">
          <div class="doc-info">
            <h3>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              {{ doc.file_name }}
            </h3>
            <div class="doc-meta">
              <span>知识库: {{ doc.collection || 'default' }}</span>
              <span>类型: {{ doc.file_type }}</span>
              <span>分块: {{ doc.total_chunks }}</span>
              <span>字符: {{ doc.total_characters }}</span>
              <span>策略: {{ doc.chunk_strategy }}</span>
              <span v-if="doc.chunk_size">大小: {{ doc.chunk_size }}</span>
              <span v-if="doc.chunk_overlap">重叠: {{ doc.chunk_overlap }}</span>
            </div>
          </div>
          <div class="doc-actions">
            <button @click="previewSourceFile(doc.doc_id, doc.file_name)" class="btn-preview" title="预览源文件">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              源文件
            </button>
            <button @click="previewChunks(doc.doc_id, doc.file_name)" class="btn-secondary" title="查看分块">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
              </svg>
              分块
            </button>
            <button @click="deleteDoc(doc.doc_id, doc.file_name)" class="btn-delete" title="删除文档">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 预览分块模态框 -->
    <div v-if="showChunkPreview" class="modal-overlay" @click="closeChunkPreview">
      <div class="modal-content chunk-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
            </svg>
            分块预览: {{ previewFileName }}
          </h3>
          <div class="modal-header-actions">
            <span class="chunk-count">共 {{ chunks.length }} 个分块</span>
            <button @click="closeChunkPreview" class="close-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="modal-body chunk-body">
          <div v-if="loadingChunks" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载分块中...</p>
          </div>
          <div v-else-if="chunks.length === 0" class="empty-state">该文档暂无分块数据</div>
          <div v-else class="chunk-list">
            <div v-if="!viewingParent" class="chunk-children-list">
              <div 
                v-for="chunk in chunks" :key="chunk.chunk_id" 
                class="chunk-card"
                @click="chunk.parent_text ? openParentView(chunk) : null"
                :class="{ 'has-parent': chunk.parent_text }"
              >
                <div class="chunk-card-header">
                  <span class="chunk-num">#{{ chunk.chunk_index + 1 }}</span>
                  <span v-if="chunk.parent_text" class="badge badge-child" title="点击查看父分块">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                    子分块
                  </span>
                  <span v-if="chunk.metadata.page" class="badge badge-page">P{{ chunk.metadata.page }}</span>
                  <span class="chunk-chars">{{ chunk.text.length }}字</span>
                </div>
                <pre class="chunk-card-text">{{ chunk.text }}</pre>
                <div v-if="chunk.parent_text" class="chunk-card-hint">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                  </svg>
                  点击可查看父分块上下文
                </div>
              </div>
            </div>
            
            <div v-else class="parent-view">
              <button class="back-btn" @click="viewingParent = null">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="19" y1="12" x2="5" y2="12"/>
                  <polyline points="12 19 5 12 12 5"/>
                </svg>
                返回分块列表
              </button>
              <div class="parent-detail">
                <div class="parent-detail-header">
                  <span class="badge badge-parent">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                      <line x1="3" y1="9" x2="21" y2="9"/>
                      <line x1="9" y1="21" x2="9" y2="9"/>
                    </svg>
                    父分块上下文
                  </span>
                  <span class="parent-chars">{{ viewingParent.parent_text.length }}字</span>
                </div>
                <pre class="parent-detail-text">{{ viewingParent.parent_text }}</pre>
                <div class="child-reference">
                  <div class="child-ref-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="11" cy="11" r="8"/>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    对应的子分块：
                  </div>
                  <pre class="child-ref-text">{{ viewingParent.text }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 源文件预览模态框 -->
    <div v-if="showFilePreview" class="modal-overlay" @click="closeFilePreview">
      <div class="modal-content file-preview-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            {{ filePreviewName }}
          </h3>
          <button @click="closeFilePreview" class="close-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body file-preview-body">
          <iframe v-if="isPdf(filePreviewName)" :src="filePreviewUrl" class="file-iframe"></iframe>
          <iframe v-else-if="isOffice(filePreviewName)" :src="filePreviewUrl" class="file-iframe"></iframe>
          <img v-else-if="isImage(filePreviewName)" :src="filePreviewUrl" class="file-image" />
          <pre v-else class="file-text-content">{{ fileTextContent }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 状态
const fileInputRef = ref(null)
const isDragOver = ref(false)
const collectionName = ref('')
const chunkStrategy = ref('recursive')
const chunkSize = ref(500)
const chunkOverlap = ref(50)
const uploadProgress = ref({
  show: false,
  percent: 0,
  text: ''
})
const documents = ref([])
const loading = ref(false)
const supportedExtensions = ['pdf', 'docx', 'xlsx', 'txt', 'md', 'png', 'jpg', 'jpeg']

// 分块预览状态
const showChunkPreview = ref(false)
const previewFileName = ref('')
const chunks = ref([])
const loadingChunks = ref(false)
const viewingParent = ref(null)

// 源文件预览状态
const showFilePreview = ref(false)
const filePreviewName = ref('')
const filePreviewUrl = ref('')
const fileTextContent = ref('')

// 加载文档列表
async function loadDocuments() {
  loading.value = true
  try {
    const res = await axios.get('/api/documents')
    documents.value = res.data.documents || []
  } catch (err) {
    console.error('加载文档失败:', err)
  } finally {
    loading.value = false
  }
}

// 触发文件选择
function triggerFileInput() {
  fileInputRef.value?.click()
}

// 处理文件选择
function handleFileSelect(e) {
  const files = e.target.files
  if (files && files.length > 0) {
    uploadFiles(Array.from(files))
  }
  e.target.value = '' // 清空文件输入值
}

// 处理拖拽
function handleDrop(e) {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer.files)
  if (files.length > 0) {
    uploadFiles(files)
  }
}

// 上传文件
async function uploadFiles(files) {
  for (const file of files) {
    await uploadFile(file)
  }
  await loadDocuments()
}

// 上传单个文件
async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  // 知识库名称：如果用户输入了则使用输入的，否则使用文件名
  let collection = collectionName.value.trim()
  if (!collection) {
    collection = file.name.replace(/\.[^/.]+$/, '')
  }
  formData.append('collection', collection)
  
  if (chunkStrategy.value) {
    formData.append('chunk_strategy', chunkStrategy.value)
  }
  
  if (chunkSize.value > 0) {
    formData.append('chunk_size', chunkSize.value)
  }
  
  if (chunkOverlap.value > 0) {
    formData.append('chunk_overlap', chunkOverlap.value)
  }
  
  uploadProgress.value = {
    show: true,
    percent: 30,
    text: `正在处理: ${file.name} (知识库: ${collection})`
  }
  
  try {
    const res = await axios.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    uploadProgress.value = {
      show: true,
      percent: 100,
      text: `成功: ${res.data.file_name} (${res.data.total_chunks} 个分块)`
    }
    
    setTimeout(() => {
      uploadProgress.value.show = false
    }, 2000)
  } catch (err) {
    uploadProgress.value = {
      show: true,
      percent: 100,
      text: `失败: ${err.response?.data?.detail || err.message}`
    }
    setTimeout(() => {
      uploadProgress.value.show = false
    }, 3000)
  }
}

// 删除文档
async function deleteDoc(docId, fileName) {
  if (!confirm(`确定要删除 "${fileName}" 吗？`)) return
  
  try {
    await axios.delete(`/api/documents/${docId}`)
    await loadDocuments()
  } catch (err) {
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 清空所有文档
async function clearAllDocuments() {
  if (!confirm('确定要清空所有文档吗？此操作不可恢复！')) return
  
  try {
    await axios.delete('/api/documents')
    await loadDocuments()
  } catch (err) {
    alert('清空失败: ' + (err.response?.data?.detail || err.message))
  }
}

// 预览分块
async function previewChunks(docId, fileName) {
  previewFileName.value = fileName
  showChunkPreview.value = true
  loadingChunks.value = true
  chunks.value = []
  viewingParent.value = null
  
  try {
    const res = await axios.get(`/api/documents/${docId}/chunks`)
    chunks.value = res.data.chunks || []
  } catch (err) {
    console.error('加载分块失败:', err)
    alert('加载分块失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loadingChunks.value = false
  }
}

// 关闭分块预览
function closeChunkPreview() {
  showChunkPreview.value = false
  chunks.value = []
  previewFileName.value = ''
  viewingParent.value = null
}

// 查看父分块
function openParentView(chunk) {
  viewingParent.value = chunk
}

// 预览源文件
async function previewSourceFile(docId, fileName) {
  filePreviewName.value = fileName
  fileTextContent.value = ''
  showFilePreview.value = true

  // DOCX / XLSX → 通过后端转 HTML 预览
  if (isOffice(fileName)) {
    filePreviewUrl.value = `/api/documents/${docId}/preview-html`
    return
  }

  // PDF / 图片 → 直接加载源文件
  filePreviewUrl.value = `/api/documents/${docId}/preview`

  // 文本类文件直接加载内容显示
  if (isTextFile(fileName)) {
    try {
      const res = await axios.get(filePreviewUrl.value, { responseType: 'text' })
      fileTextContent.value = res.data
    } catch (err) {
      fileTextContent.value = '加载失败: ' + (err.message)
    }
  }
}

// 关闭源文件预览
function closeFilePreview() {
  showFilePreview.value = false
  filePreviewName.value = ''
  filePreviewUrl.value = ''
  fileTextContent.value = ''
}

// 文件类型判断
function isPdf(name) {
  return /\.pdf$/i.test(name)
}
function isImage(name) {
  return /\.(png|jpe?g|gif|webp|bmp|tiff?)$/i.test(name)
}
function isTextFile(name) {
  return /\.(txt|md|csv|json|xml|html|log)$/i.test(name)
}
function isOffice(name) {
  return /\.(docx?|xlsx?)$/i.test(name)
}

// 初始化
onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.upload-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

/* ===== 头部 ===== */
.upload-header {
  padding: 24px 28px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  backdrop-filter: var(--blur-md);
}

.upload-header h1 {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.upload-header p {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

/* ===== 上传区域 ===== */
.upload-section {
  padding: 24px 28px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
}

.upload-zone {
  border: 2px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  background: var(--bg-hover);
  position: relative;
  overflow: hidden;
}

.upload-zone::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--primary-bg), var(--accent-bg));
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.upload-zone:hover::before,
.upload-zone.drag-over::before {
  opacity: 1;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--primary);
  background: var(--primary-bg);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px var(--primary-shadow), 0 0 40px var(--primary-bg);
}

.upload-zone.drag-over {
  animation: zoneGlow 1.5s ease-in-out infinite;
}

@keyframes zoneGlow {
  0%, 100% { box-shadow: 0 8px 32px var(--primary-shadow), 0 0 40px var(--primary-bg); }
  50% { box-shadow: 0 8px 40px var(--primary-bg-hover), 0 0 60px var(--primary-bg); }
}

.upload-icon {
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
  color: var(--primary);
  opacity: 0.7;
  transition: all var(--transition-normal);
}

.upload-zone:hover .upload-icon,
.upload-zone.drag-over .upload-icon {
  opacity: 1;
  transform: translateY(-4px);
}

.upload-zone p {
  margin: 6px 0;
  color: var(--text-secondary);
  font-size: 14px;
  position: relative;
  z-index: 1;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted) !important;
}

/* ===== 上传选项 ===== */
.upload-options {
  display: flex;
  gap: 16px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-group label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.option-group input,
.option-group select {
  padding: 8px 12px;
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-sm);
  font-size: 13px;
  outline: none;
  background: var(--bg-hover);
  color: var(--text-primary);
  transition: all var(--transition-normal);
  width: 110px;
}

.option-group input:focus,
.option-group select:focus {
  border-color: var(--primary);
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.option-group select option {
  background: var(--bg-base);
  color: var(--text-primary);
}

/* ===== 上传进度 ===== */
.upload-progress {
  padding: 16px 28px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  animation: slideDown 0.3s ease;
}

.progress-bar {
  height: 6px;
  background: var(--bg-hover);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--primary));
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
  transition: width 0.3s ease;
  border-radius: 3px;
  box-shadow: 0 0 12px var(--primary-glow);
}

.upload-progress p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

/* ===== 文档列表 ===== */
.doc-list-section {
  padding: 24px 28px;
  flex: 1;
  overflow-y: auto;
}

.doc-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.doc-list-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-list-header h2 svg {
  color: var(--primary);
}

/* ===== 按钮 ===== */
.btn-danger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-normal);
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: var(--accent-bg);
  color: var(--accent-light);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-normal);
}

.btn-secondary:hover {
  background: var(--accent-bg-hover);
  border-color: var(--accent-border-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--accent-glow);
}

.btn-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: var(--primary-bg);
  color: var(--primary-light);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-normal);
}

.btn-preview:hover {
  background: var(--primary-bg-hover);
  border-color: var(--primary-border-strong);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--primary-glow);
}

.btn-delete {
  padding: 7px 10px;
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--danger);
}

.doc-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ===== 状态 ===== */
.loading-state,
.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--text-muted);
  font-size: 14px;
}

.empty-state svg {
  margin-bottom: 12px;
  opacity: 0.3;
  color: var(--text-muted);
}

.empty-state p {
  margin: 0;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

/* ===== 文档卡片 ===== */
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.doc-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-hover);
  transition: all var(--transition-normal);
}

.doc-card:hover {
  border-color: var(--primary-border);
  background: var(--primary-bg);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md), 0 0 20px var(--primary-bg);
}

.doc-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-info h3 svg {
  color: var(--primary);
  opacity: 0.6;
  flex-shrink: 0;
}

.doc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.doc-meta span {
  background: var(--bg-surface);
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  border: 1px solid var(--border-subtle);
}

/* ===== 模态框 ===== */
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

.chunk-modal {
  max-width: 920px;
  width: 95%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), 0 0 40px var(--primary-bg);
  animation: scaleIn 0.25s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-header h3 svg {
  color: var(--primary);
}

.modal-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chunk-count {
  font-size: 12px;
  color: var(--text-tertiary);
  background: var(--bg-hover);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
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

/* ===== 分块内容 ===== */
.chunk-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chunk-children-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chunk-card {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  background: var(--bg-hover);
  transition: all var(--transition-normal);
}

.chunk-card:hover {
  border-color: var(--primary-border);
  box-shadow: 0 4px 16px var(--primary-bg);
}

.chunk-card.has-parent {
  cursor: pointer;
  border-left: 3px solid var(--success);
  background: rgba(16, 185, 129, 0.04);
}

.chunk-card.has-parent:hover {
  border-color: rgba(16, 185, 129, 0.3);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.08);
  transform: translateY(-2px);
}

.chunk-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.chunk-num {
  font-weight: 700;
  font-size: 13px;
  color: var(--accent-light);
  background: var(--accent-bg-hover);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
}

.chunk-chars {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}

.chunk-card-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.15);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin: 0;
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid var(--border-subtle);
}

.chunk-card-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--success);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0.8;
}

/* ===== 徽章 ===== */
.badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.badge-child {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.badge-page {
  background: var(--primary-bg-hover);
  color: var(--primary-light);
}

.badge-parent {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* ===== 父分块视图 ===== */
.parent-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border-normal);
  border-radius: var(--radius-sm);
  background: var(--bg-hover);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all var(--transition-normal);
  align-self: flex-start;
}

.back-btn:hover {
  border-color: var(--primary-border-hover);
  background: var(--primary-bg);
  color: var(--primary-light);
}

.parent-detail {
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: var(--radius-lg);
  background: rgba(245, 158, 11, 0.04);
  padding: 20px;
}

.parent-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.parent-chars {
  font-size: 12px;
  color: var(--text-tertiary);
  background: var(--bg-hover);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
}

.parent-detail-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.12);
  padding: 16px;
  border-radius: var(--radius-md);
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
}

.child-reference {
  margin-top: 16px;
  border-top: 1px dashed var(--border-normal);
  padding-top: 14px;
}

.child-ref-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.child-ref-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  color: var(--success);
  background: rgba(16, 185, 129, 0.06);
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--success);
  margin: 0;
}

/* ===== 源文件预览模态框 ===== */
.file-preview-modal {
  width: 98vw;
  height: 96vh;
  max-width: none;
  max-height: none;
  display: flex;
  flex-direction: column;
}

.file-preview-modal .modal-header {
  flex-shrink: 0;
  padding: 14px 20px;
}

.file-preview-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
  min-height: 0;
  display: flex;
}

.file-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.file-image {
  max-width: 100%;
  max-height: 92vh;
  object-fit: contain;
  margin: auto;
  display: block;
  padding: 16px;
}

.file-text-content {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 20px 24px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.2);
  overflow-y: auto;
}
</style>
