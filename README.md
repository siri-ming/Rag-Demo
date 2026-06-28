# RAG Demo

基于 FastAPI + PostgreSQL (pgvector) + Vue.js 3 构建的企业级 RAG（检索增强生成）知识库问答系统。支持多格式文档上传、OCR 识别、多种分块策略，提供现代化 Web 界面，支持流式实时输出和多主题切换。

## 快速开始

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.12+ | 后端运行环境 |
| Node.js | 16+ | 前端构建（仅开发时需要） |
| PostgreSQL | 14+ | 需安装 pgvector 扩展 |
| uv | 最新 | Python 包管理器 |

### 1. 启动数据库

推荐使用 Docker 一键启动：

```bash
docker run -d --name rag-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，**必填项**：
- `DASHSCOPE_API_KEY` — 阿里云百炼 API Key，从 [百炼控制台](https://bailian.console.aliyun.com/) 获取

其他配置项见下方 [配置说明](#配置说明)。

### 3. 安装后端依赖

```bash
uv sync
```

### 4. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

构建产物会自动输出到 `app/static/dist/` 目录，后端启动后直接提供静态文件服务。

### 5. 启动后端服务

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 启动前端服务

```bash
cd frontend
npm run build
npm run dev
```

浏览器访问 **http://localhost:5173** 即可使用。

### 前端开发模式（可选）

如果你需要修改前端代码并实时预览，可以启动 Vite 开发服务器：

```bash
cd frontend
npm run dev
```

前端开发服务器运行在 **http://localhost:5173**，会自动将 `/api` 请求代理到后端 `localhost:8000`。

> **注意**：生产环境不需要启动前端开发服务器，只需 `npm run build` 构建后由后端统一提供服务即可。

## 项目架构

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   用户浏览器   │ ───▶ │  Vue.js 前端   │ ───▶ │  FastAPI 后端  │
│  (端口 8000)  │      │ (开发: 5173)  │      │  (端口 8000)  │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          │                        │                        │
                   ┌──────▼──────┐   ┌────────────▼───┐   ┌──────────────▼──┐
                   │ 文档解析器    │   │  向量嵌入服务   │   │  LLM 对话服务   │
                   │ PDF/Word/图片│   │ text-embedding │   │  通义千问模型    │
                   └──────┬──────┘   └────────────┬───┘   └─────────────────┘
                          │                        │
                   ┌──────▼────────────────────────▼───┐
                   │     PostgreSQL + pgvector          │
                   │   (文档存储 + 向量检索)              │
                   └───────────────────────────────────┘
```

## 功能特性

### 文档管理
- **多格式支持**：PDF、Word (.docx)、Excel (.xlsx)、Markdown、纯文本、图片 (OCR)
- **灵活分块**：递归分块 (recursive)、固定大小分块 (fixed_size)、父子分块 (parent_child)
- **分块预览**：可视化查看文档分块结果，方便调优分块参数
- **知识库管理**：按知识库名称组织文档，支持多知识库隔离与联合查询

### 智能问答
- **流式输出**：基于 SSE 的实时逐字生成，打字机效果
- **停止生成**：随时中断正在进行的流式响应
- **来源追溯**：查看回答引用的文档片段，包含相关度评分和页码
- **多知识库查询**：支持选择特定知识库或全部知识库进行检索
- **相关度过滤**：可调节相关度阈值，过滤低相关性结果

### 界面体验
- **多主题切换**：内置暗色、亮色、赛博朋克、自然 4 套主题皮肤
- **响应式布局**：适配不同屏幕尺寸
- **玻璃拟态设计**：现代化的 UI 视觉风格

## 项目结构

```
rag-demo/
├── app/
│   ├── api/                  # API 路由与数据模型
│   │   ├── routes/
│   │   │   ├── chat.py       # 对话相关接口
│   │   │   └── document.py   # 文档管理接口
│   │   └── schemas.py        # 请求/响应数据结构定义
│   ├── core/                 # 核心服务
│   │   ├── database.py       # PostgreSQL 数据库连接与初始化
│   │   ├── embedding.py      # 向量嵌入服务
│   │   ├── llm.py            # 大语言模型服务
│   │   └── vectorstore.py    # pgvector 向量存储
│   ├── parsers/              # 文档解析器（PDF/Word/Excel/图片/文本）
│   ├── chunkers/             # 分块策略（递归/固定/父子）
│   ├── services/             # 业务逻辑层（文档服务/RAG 服务）
│   ├── static/dist/          # 前端构建产物（由 Vite 自动输出）
│   └── config.py             # 全局配置管理
├── frontend/                 # 前端源码（Vue.js 3 + Vite）
│   ├── src/
│   │   ├── assets/style.css  # 主题变量与全局样式
│   │   ├── views/
│   │   │   ├── ChatView.vue  # 聊天问答界面
│   │   │   └── UploadView.vue# 文档管理界面
│   │   ├── App.vue           # 主布局与导航
│   │   └── main.js           # 前端入口
│   ├── vite.config.js        # Vite 配置（含代理与构建输出）
│   └── package.json
├── uploads/                  # 上传的原始文件存储目录
├── main.py                   # 应用入口（FastAPI 初始化）
├── .env                      # 环境变量配置（不提交到 Git）
├── .env.example              # 环境变量示例
└── pyproject.toml            # Python 依赖配置
```

## 配置说明

所有配置项在 `.env` 文件中设置：

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key | — | 是 |
| `DASHSCOPE_LLM_MODEL` | 对话模型名称 | `qwen-plus` | 否 |
| `DASHSCOPE_EMBEDDING_MODEL` | 向量嵌入模型 | `text-embedding-v3` | 否 |
| `DASHSCOPE_BASE_URL` | DashScope 兼容接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 否 |
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://postgres:postgres@localhost:5432/rag_db` | 否 |
| `EMBEDDING_DIM` | 向量维度（需与模型一致） | `1024` | 否 |
| `UPLOAD_DIR` | 上传文件存储目录 | `./uploads` | 否 |

> **分块参数**（chunk_size、chunk_overlap、chunk_strategy）在前端上传文档时指定，无需通过环境变量配置。

## API 接口

### 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/documents/upload` | 上传并处理文档 |
| `GET` | `/api/documents` | 获取所有已上传文档列表 |
| `GET` | `/api/documents/collections` | 获取知识库列表 |
| `GET` | `/api/documents/{doc_id}/chunks` | 查看文档分块详情 |
| `GET` | `/api/documents/{doc_id}/preview` | 预览文档源文件 |
| `DELETE` | `/api/documents/{doc_id}` | 删除指定文档 |
| `DELETE` | `/api/documents` | 清空所有文档和知识库 |

### 智能问答

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/chat` | 非流式问答（一次性返回完整结果） |
| `POST` | `/api/chat/stream` | 流式问答（SSE 实时推送） |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |

## 常见问题

### 页面白屏
前端未构建或构建产物路径不对。执行：
```bash
cd frontend && npm run build
```

### 数据库连接失败
确认 PostgreSQL 正在运行，且已安装 pgvector 扩展：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### API Key 未配置
确认 `.env` 文件中 `DASHSCOPE_API_KEY` 已正确填写。

### 项目重命名后 uv 启动报错
如果重命名了项目文件夹，需要删除 `.venv` 后重新执行 `uv sync`，因为虚拟环境中的脚本路径是绝对路径。

## License

MIT License
