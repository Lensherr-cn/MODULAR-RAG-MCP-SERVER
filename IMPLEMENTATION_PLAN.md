# 企业内部文档知识库 - 实施计划

> 基于 Modular RAG MCP Server 项目，构建企业内部文档知识库系统

---

## 一、项目目标

构建一个支持多格式文档、多 LLM Provider 的企业内部知识库系统：

- **文档格式**：PDF、Word、Markdown
- **LLM Provider**：DeepSeek、千问(Qwen)、GLM(智谱)
- **部署方式**：服务器部署，团队共享使用
- **核心功能**：文档摄取、语义检索、智能问答

### 前端界面需求

系统需要**两套前端界面**：

| 界面 | 目标用户 | 功能 |
|------|----------|------|
| **管理后台** | 系统管理员 | 文档上传、数据管理、系统配置、日志查看 |
| **知识库前台** | 普通员工 | 文档检索、智能问答、知识浏览 |

**现有 Dashboard 是管理后台**，需要**新增知识库前台**。

---

## 二、现状分析

### 2.1 已有能力

| 模块 | 状态 | 说明 |
|------|------|------|
| DeepSeek LLM | ✅ 已实现 | `src/libs/llm/deepseek_llm.py` |
| OpenAI LLM | ✅ 已实现 | `src/libs/llm/openai_llm.py` |
| Azure LLM | ✅ 已实现 | `src/libs/llm/azure_llm.py` |
| Ollama LLM | ✅ 已实现 | `src/libs/llm/ollama_llm.py` |
| PDF Loader | ✅ 已实现 | `src/libs/loader/pdf_loader.py` |
| OpenAI Embedding | ✅ 已实现 | `src/libs/embedding/openai_embedding.py` |
| Azure Embedding | ✅ 已实现 | `src/libs/embedding/azure_embedding.py` |
| Ollama Embedding | ✅ 已实现 | `src/libs/embedding/ollama_embedding.py` |
| Hybrid Search | ✅ 已实现 | BM25 + Dense + RRF Fusion |
| MCP Server | ✅ 已实现 | 标准 MCP 协议 |
| Dashboard | ✅ 已实现 | Streamlit 管理界面 |

### 2.2 待开发能力

| 模块 | 优先级 | 工作量 |
|------|--------|--------|
| **知识库前台界面** | P0 | 2天 |
| 千问(Qwen) LLM Provider | P1 | 0.5天 |
| GLM(智谱) LLM Provider | P1 | 0.5天 |
| 千问 Embedding Provider | P1 | 0.5天 |
| Word Loader | P1 | 0.5天 |
| Markdown Loader | P1 | 0.5天 |
| Docker 部署配置 | P1 | 0.5天 |
| 部署文档 | P2 | 0.5天 |

---

## 三、前端界面设计

### 3.1 现有 Dashboard（管理后台）

项目已有 Streamlit Dashboard，包含 6 个页面：

| 页面 | 功能 |
|------|------|
| Overview | 系统配置概览、Collection 统计 |
| Data Browser | 浏览文档、Chunk、图片 |
| Ingestion Manager | 上传文档、触发摄取、删除文档 |
| Ingestion Traces | 摄取链路追踪日志 |
| Query Traces | 查询链路追踪日志 |
| Evaluation Panel | RAG 评估面板 |

**定位**：面向系统管理员的运维工具

### 3.2 新增：知识库前台界面

**定位**：面向普通员工的知识查询工具

#### 页面结构

```
知识库前台
├── 首页（Dashboard）
│   ├── 快速搜索框
│   ├── 热门问题推荐
│   └── 最近更新文档
│
├── 智能问答
│   ├── 对话式问答界面
│   ├── 引用来源展示
│   └── 相关文档推荐
│
├── 文档中心
│   ├── 文档分类浏览
│   ├── 文档搜索
│   └── 文档详情预览
│
└── 个人中心
    ├── 查询历史
    ├── 收藏文档
    └── 反馈记录
```

#### 技术选型

| 方案 | 框架 | 优点 | 缺点 |
|------|------|------|------|
| **方案A** | Streamlit | 与现有 Dashboard 一致，开发快 | 交互能力有限，不够美观 |
| **方案B** | Gradio | 适合对话类应用，开发快 | 定制性一般 |
| **方案C** | FastAPI + Vue/React | 界面美观，交互丰富，可定制性强 | 开发周期长 |

**推荐方案**：**方案A（Streamlit）** - 快速上线，后续可升级

#### 详细页面设计

##### 页面1：首页（Home）

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 企业知识库                              [用户名] [设置]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         ┌─────────────────────────────────────────┐        │
│         │  🔍 搜索你想了解的知识...              │        │
│         └─────────────────────────────────────────┘        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  📌 热门问题                    📚 最近更新                  │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │ • 报销流程是什么？    │      │ 产品手册 v2.0        │    │
│  │ • 如何申请年假？      │      │ 技术规范文档         │    │
│  │ • 公司福利有哪些？    │      │ 培训资料更新         │    │
│  └──────────────────────┘      └──────────────────────┘    │
│                                                             │
│  📊 知识库统计                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 文档总数  │ │ 今日问答  │ │ 热门文档  │ │ 用户数    │      │
│  │   156    │ │    42    │ │   23     │ │   38     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

##### 页面2：智能问答（Chat）

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 企业知识库 > 智能问答                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 👤 请问公司的报销流程是什么？                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🤖 根据公司财务制度，报销流程如下：                   │   │
│  │                                                     │   │
│  │ 1. 填写报销单（需附发票原件）                        │   │
│  │ 2. 部门主管审批                                     │   │
│  │ 3. 财务审核                                         │   │
│  │ 4. 打款至工资卡                                     │   │
│  │                                                     │   │
│  │ 📎 引用来源：                                       │   │
│  │ • 财务管理制度.pdf (第12-15页)                      │   │
│  │ • 报销流程说明.docx                                 │   │
│  │                                                     │   │
│  │ 👍 有帮助  👎 无帮助  📋 复制  📤 分享              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  💡 相关问题推荐：                                          │
│  • 发票抬头怎么填写？                                       │
│  • 差旅费报销标准是多少？                                   │
│  • 报销审批需要多长时间？                                   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [🔍 输入你的问题...]                        [发送]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

##### 页面3：文档中心（Documents）

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 企业知识库 > 文档中心                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [🔍 搜索文档...]           [全部分类 ▼]  [全部类型 ▼]      │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  📁 产品文档 (12)    📁 技术文档 (23)    📁 规章制度 (8)    │
│  📁 培训资料 (15)    📁 流程规范 (10)    📁 其他 (5)        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  📄 文档列表                                                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📑 产品使用手册 v2.0.pdf                            │   │
│  │    产品文档 · 2.3MB · 更新于 2024-03-15             │   │
│  │    [预览] [下载] [收藏]                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📑 技术架构设计文档.docx                            │   │
│  │    技术文档 · 1.8MB · 更新于 2024-03-10             │   │
│  │    [预览] [下载] [收藏]                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📑 员工手册2024版.pdf                               │   │
│  │    规章制度 · 3.1MB · 更新于 2024-03-01             │   │
│  │    [预览] [下载] [收藏]                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [上一页] 1 2 3 ... 10 [下一页]                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

##### 页面4：个人中心（Profile）

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 企业知识库 > 个人中心                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👤 用户信息                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 用户名：张三                                         │   │
│  │ 部门：技术部                                         │   │
│  │ 注册时间：2024-01-15                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📜 查询历史（最近10条）                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • 报销流程是什么？           2024-03-15 14:30       │   │
│  │ • 如何申请年假？             2024-03-14 10:20       │   │
│  │ • 技术架构文档在哪？         2024-03-13 16:45       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ⭐ 收藏文档                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📑 产品使用手册 v2.0.pdf                            │   │
│  │ 📑 技术架构设计文档.docx                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📝 我的反馈                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ "报销流程回答很有帮助" 👍    2024-03-15             │   │
│  │ "年假申请流程需要更新" 💬    2024-03-14             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 技术选型：Vue.js + FastAPI

采用**前后端分离架构**：

```
┌──────────────────────┐                    ┌──────────────────────┐
│   Vue 3 前端          │                    │   FastAPI 后端        │
│   (用户界面)          │  ←── REST API ──→  │   (业务逻辑)          │
├──────────────────────┤                    ├──────────────────────┤
│ • Vue 3 + Vite       │                    │ • FastAPI            │
│ • Element Plus (UI)  │                    │ • Pydantic           │
│ • Pinia (状态管理)    │                    │ • 现有 RAG 模块       │
│ • Vue Router         │                    │ • MCP Server         │
│ • Axios              │                    │ • ChromaDB           │
└──────────────────────┘                    └──────────────────────┘
        ↓                                            ↓
   端口: 80/443                                端口: 8000
```

### 3.4 后端 API 设计

#### API 接口清单

| 模块 | 接口 | 方法 | 说明 |
|------|------|------|------|
| **问答** | `/api/v1/chat` | POST | 智能问答（流式响应） |
| | `/api/v1/chat/history` | GET | 获取对话历史 |
| **文档** | `/api/v1/documents` | GET | 文档列表（分页、筛选） |
| | `/api/v1/documents/{id}` | GET | 文档详情 |
| | `/api/v1/documents/upload` | POST | 上传文档 |
| | `/api/v1/documents/{id}` | DELETE | 删除文档 |
| | `/api/v1/categories` | GET | 文档分类列表 |
| **搜索** | `/api/v1/search` | GET | 全局搜索 |
| **统计** | `/api/v1/stats/overview` | GET | 首页统计数据 |
| | `/api/v1/stats/hot-questions` | GET | 热门问题 |
| **用户** | `/api/v1/user/profile` | GET | 用户信息 |
| | `/api/v1/user/history` | GET | 查询历史 |
| | `/api/v1/user/favorites` | GET | 收藏列表 |
| | `/api/v1/user/favorites/{id}` | POST/DELETE | 添加/取消收藏 |
| **反馈** | `/api/v1/feedback` | POST | 提交反馈 |

#### API 详细设计

**1. 智能问答接口**

```yaml
POST /api/v1/chat
Request:
  {
    "query": "公司的报销流程是什么？",
    "collection": "default",      # 可选，指定知识库
    "conversation_id": "uuid",    # 可选，多轮对话
    "stream": true                # 是否流式响应
  }

Response (非流式):
  {
    "answer": "根据公司财务制度，报销流程如下...",
    "sources": [
      {
        "document_id": "doc_001",
        "document_name": "财务管理制度.pdf",
        "chunk_id": "chunk_012",
        "content": "相关段落内容...",
        "page": 12,
        "score": 0.95
      }
    ],
    "related_questions": [
      "发票抬头怎么填写？",
      "差旅费报销标准是多少？"
    ],
    "conversation_id": "uuid"
  }

Response (流式 SSE):
  data: {"type": "token", "content": "根据"}
  data: {"type": "token", "content": "公司"}
  data: {"type": "sources", "sources": [...]}
  data: {"type": "done"}
```

**2. 文档列表接口**

```yaml
GET /api/v1/documents?page=1&page_size=20&category=产品文档&keyword=手册

Response:
  {
    "total": 156,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "doc_001",
        "name": "产品使用手册 v2.0.pdf",
        "category": "产品文档",
        "file_type": "pdf",
        "file_size": 2457600,
        "chunk_count": 45,
        "created_at": "2024-03-15T10:30:00Z",
        "updated_at": "2024-03-15T10:30:00Z"
      }
    ]
  }
```

**3. 首页统计接口**

```yaml
GET /api/v1/stats/overview

Response:
  {
    "document_count": 156,
    "chunk_count": 3420,
    "today_queries": 42,
    "total_queries": 1250,
    "active_users": 38,
    "categories": [
      {"name": "产品文档", "count": 12},
      {"name": "技术文档", "count": 23},
      {"name": "规章制度", "count": 8}
    ]
  }
```

### 3.5 前端架构设计

#### 项目结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/                    # API 接口封装
│   │   ├── index.ts            # Axios 实例配置
│   │   ├── chat.ts             # 问答相关 API
│   │   ├── document.ts         # 文档相关 API
│   │   ├── search.ts           # 搜索相关 API
│   │   └── user.ts             # 用户相关 API
│   │
│   ├── components/             # 通用组件
│   │   ├── common/
│   │   │   ├── AppHeader.vue   # 顶部导航
│   │   │   ├── AppSidebar.vue  # 侧边栏
│   │   │   ├── SearchBox.vue   # 搜索框
│   │   │   └── Loading.vue     # 加载状态
│   │   ├── chat/
│   │   │   ├── ChatMessage.vue # 对话消息
│   │   │   ├── ChatInput.vue   # 输入框
│   │   │   ├── SourceCard.vue  # 引用来源卡片
│   │   │   └── RelatedQuestions.vue  # 相关问题
│   │   └── document/
│   │       ├── DocCard.vue     # 文档卡片
│   │       ├── DocPreview.vue  # 文档预览
│   │       └── CategoryTree.vue # 分类树
│   │
│   ├── views/                  # 页面视图
│   │   ├── HomeView.vue        # 首页
│   │   ├── ChatView.vue        # 智能问答
│   │   ├── DocumentsView.vue   # 文档中心
│   │   ├── DocumentDetailView.vue  # 文档详情
│   │   └── ProfileView.vue     # 个人中心
│   │
│   ├── stores/                 # Pinia 状态管理
│   │   ├── index.ts
│   │   ├── chat.ts             # 对话状态
│   │   ├── document.ts         # 文档状态
│   │   └── user.ts             # 用户状态
│   │
│   ├── router/                 # 路由配置
│   │   └── index.ts
│   │
│   ├── styles/                 # 样式文件
│   │   ├── variables.scss      # 变量定义
│   │   └── global.scss         # 全局样式
│   │
│   ├── utils/                  # 工具函数
│   │   ├── request.ts          # 请求封装
│   │   └── storage.ts          # 本地存储
│   │
│   ├── App.vue                 # 根组件
│   └── main.ts                 # 入口文件
│
├── index.html
├── vite.config.ts              # Vite 配置
├── tsconfig.json               # TypeScript 配置
├── package.json
└── .env                        # 环境变量
```

#### 页面路由

```typescript
// router/index.ts
const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/chat', name: 'chat', component: ChatView },
  { path: '/documents', name: 'documents', component: DocumentsView },
  { path: '/documents/:id', name: 'document-detail', component: DocumentDetailView },
  { path: '/profile', name: 'profile', component: ProfileView },
]
```

#### 技术栈详情

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue 3 | ^3.4 | Composition API |
| 构建 | Vite | ^5.0 | 快速构建 |
| UI | Element Plus | ^2.5 | 企业级 UI 组件库 |
| 状态 | Pinia | ^2.1 | Vue 官方状态管理 |
| 路由 | Vue Router | ^4.2 | 路由管理 |
| HTTP | Axios | ^1.6 | HTTP 客户端 |
| 样式 | SCSS | - | CSS 预处理器 |
| 语言 | TypeScript | ^5.0 | 类型安全 |

### 3.6 后端架构设计

#### 项目结构

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py             # 依赖注入
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # 路由汇总
│   │   │   ├── chat.py         # 问答接口
│   │   │   ├── documents.py    # 文档接口
│   │   │   ├── search.py       # 搜索接口
│   │   │   ├── stats.py        # 统计接口
│   │   │   └── user.py         # 用户接口
│   │
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── document.py
│   │   ├── user.py
│   │   └── common.py
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── chat_service.py     # 问答服务
│   │   ├── document_service.py # 文档服务
│   │   ├── search_service.py   # 搜索服务
│   │   └── user_service.py     # 用户服务
│   │
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   └── security.py         # 安全相关
│   │
│   └── main.py                 # FastAPI 入口
│
├── src/                        # 现有 RAG 模块（复用）
│   ├── core/
│   ├── libs/
│   ├── ingestion/
│   └── ...
│
├── requirements.txt
└── .env
```

#### FastAPI 主入口

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(
    title="Enterprise Knowledge Hub API",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3.7 前端页面设计（Vue 实现）

#### 首页（HomeView.vue）

```vue
<template>
  <div class="home-view">
    <!-- 顶部搜索区 -->
    <div class="hero-section">
      <h1>🏢 企业知识库</h1>
      <SearchBox
        v-model="searchQuery"
        placeholder="搜索你想了解的知识..."
        @search="handleSearch"
      />
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover">
          <el-statistic :title="stat.label" :value="stat.value" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 热门问题 & 最近更新 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card header="📌 热门问题">
          <el-list>
            <el-list-item
              v-for="q in hotQuestions"
              :key="q.id"
              @click="goToChat(q.question)"
            >
              {{ q.question }}
            </el-list-item>
          </el-list>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="📚 最近更新">
          <DocCard
            v-for="doc in recentDocs"
            :key="doc.id"
            :document="doc"
            @click="goToDocument(doc.id)"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

#### 智能问答（ChatView.vue）

```vue
<template>
  <div class="chat-view">
    <!-- 对话历史 -->
    <div class="chat-messages" ref="messagesContainer">
      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
      <div v-if="loading" class="loading-indicator">
        <el-icon class="is-loading"><Loading /></el-icon>
        正在思考中...
      </div>
    </div>

    <!-- 引用来源 -->
    <div v-if="currentSources.length" class="sources-panel">
      <h4>📎 引用来源</h4>
      <SourceCard
        v-for="source in currentSources"
        :key="source.chunk_id"
        :source="source"
      />
    </div>

    <!-- 相关问题 -->
    <RelatedQuestions
      v-if="relatedQuestions.length"
      :questions="relatedQuestions"
      @select="handleQuestionSelect"
    />

    <!-- 输入框 -->
    <ChatInput
      v-model="inputText"
      :disabled="loading"
      @send="handleSend"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { chatApi } from '@/api/chat'
import type { ChatMessage, Source } from '@/types'

const messages = ref<ChatMessage[]>([])
const currentSources = ref<Source[]>([])
const relatedQuestions = ref<string[]>([])
const inputText = ref('')
const loading = ref(false)

const handleSend = async () => {
  if (!inputText.value.trim()) return

  const query = inputText.value
  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  loading.value = true

  try {
    const response = await chatApi.query({ query })
    messages.value.push({ role: 'assistant', content: response.answer })
    currentSources.value = response.sources
    relatedQuestions.value = response.related_questions
  } finally {
    loading.value = false
  }
}
</script>
```

### 3.8 开发任务清单

#### 后端开发任务

| 任务 | 文件 | 说明 |
|------|------|------|
| FastAPI 项目初始化 | `app/main.py` | 入口文件、CORS 配置 |
| API 路由定义 | `app/api/v1/router.py` | 路由汇总 |
| 问答接口 | `app/api/v1/chat.py` | POST /chat，支持流式 |
| 文档接口 | `app/api/v1/documents.py` | CRUD 接口 |
| 搜索接口 | `app/api/v1/search.py` | 全局搜索 |
| 统计接口 | `app/api/v1/stats.py` | 首页数据 |
| 用户接口 | `app/api/v1/user.py` | 历史、收藏 |
| Pydantic 模型 | `app/schemas/*.py` | 请求/响应模型 |
| 业务服务层 | `app/services/*.py` | 封装业务逻辑 |
| 启动脚本 | `scripts/start_api.py` | 启动 FastAPI |

#### 前端开发任务

| 任务 | 文件 | 说明 |
|------|------|------|
| Vue 项目初始化 | `frontend/` | Vite + Vue 3 + TS |
| API 封装 | `src/api/*.ts` | Axios 实例、接口封装 |
| 通用组件 | `src/components/common/` | Header、Sidebar、SearchBox |
| 对话组件 | `src/components/chat/` | ChatMessage、ChatInput、SourceCard |
| 文档组件 | `src/components/document/` | DocCard、CategoryTree |
| 首页 | `src/views/HomeView.vue` | 搜索、统计、推荐 |
| 智能问答 | `src/views/ChatView.vue` | 对话界面 |
| 文档中心 | `src/views/DocumentsView.vue` | 文档列表、分类 |
| 个人中心 | `src/views/ProfileView.vue` | 历史、收藏 |
| 状态管理 | `src/stores/*.ts` | Pinia stores |
| 路由配置 | `src/router/index.ts` | Vue Router |

### 阶段一：环境配置与基础测试（Day 1）

#### 1.1 配置 DeepSeek Provider

**目标**：使用已有的 DeepSeek 实现，完成基础配置

**步骤**：

1. 修改 `config/settings.yaml`：
```yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"  # 或 "deepseek-coder"
  api_key: "${DEEPSEEK_API_KEY}"  # 从环境变量读取
  temperature: 0.0
  max_tokens: 4096

embedding:
  provider: "openai"  # DeepSeek 暂无 embedding，使用 OpenAI 或其他
  model: "text-embedding-ada-002"
  api_key: "${OPENAI_API_KEY}"
  dimensions: 1536
```

2. 设置环境变量：
```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export OPENAI_API_KEY="your-openai-api-key"  # 用于 embedding
```

3. 注册 DeepSeek Provider（在 `src/libs/llm/__init__.py` 中）：
```python
from src.libs.llm.deepseek_llm import DeepSeekLLM
from src.libs.llm.llm_factory import LLMFactory
LLMFactory.register_provider("deepseek", DeepSeekLLM)
```

**验证命令**：
```bash
# 测试 LLM 连接
python -c "
from src.core.settings import load_settings
from src.libs.llm.llm_factory import LLMFactory
settings = load_settings()
llm = LLMFactory.create(settings)
print(llm.chat([{'role': 'user', 'content': 'Hello'}]).content)
"
```

#### 1.2 测试 PDF 摄取

**步骤**：

1. 准备测试文档：
```bash
mkdir -p data/documents
# 放入几个 PDF 文件
```

2. 执行摄取：
```bash
python scripts/ingest.py --path data/documents/ --collection test_docs -v
```

3. 测试检索：
```bash
python scripts/query.py --query "文档中的关键内容" --collection test_docs
```

---

### 阶段二：扩展 LLM Provider（Day 2）

#### 2.1 新增千问(Qwen) Provider

**文件**：`src/libs/llm/qwen_llm.py`

**实现要点**：
- 千问 API 兼容 OpenAI 格式
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 模型：`qwen-turbo`、`qwen-plus`、`qwen-max`
- 环境变量：`QWEN_API_KEY`

**代码框架**：
```python
class QwenLLM(BaseLLM):
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, settings, api_key=None, base_url=None, **kwargs):
        self.model = settings.llm.model
        self.api_key = api_key or os.environ.get("QWEN_API_KEY")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        # ... 其余实现参考 DeepSeekLLM
```

#### 2.2 新增 GLM(智谱) Provider

**文件**：`src/libs/llm/glm_llm.py`

**实现要点**：
- GLM API 兼容 OpenAI 格式
- Base URL: `https://open.bigmodel.cn/api/paas/v4`
- 模型：`glm-4`、`glm-4-flash`、`glm-3-turbo`
- 环境变量：`GLM_API_KEY`

**代码框架**：
```python
class GLMLLM(BaseLLM):
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, settings, api_key=None, base_url=None, **kwargs):
        self.model = settings.llm.model
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        # ... 其余实现参考 DeepSeekLLM
```

#### 2.3 新增千问 Embedding Provider

**文件**：`src/libs/embedding/qwen_embedding.py`

**实现要点**：
- API: `https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings`
- 模型：`text-embedding-v1`、`text-embedding-v2`
- 维度：1536

#### 2.4 注册新 Provider

**文件**：`src/libs/llm/__init__.py`

```python
# 注册千问
from src.libs.llm.qwen_llm import QwenLLM
LLMFactory.register_provider("qwen", QwenLLM)

# 注册 GLM
from src.libs.llm.glm_llm import GLMLLM
LLMFactory.register_provider("glm", GLMLLM)
```

**文件**：`src/libs/embedding/__init__.py`

```python
# 注册千问 Embedding
from src.libs.embedding.qwen_embedding import QwenEmbedding
EmbeddingFactory.register_provider("qwen", QwenEmbedding)
```

---

### 阶段三：扩展文档格式（Day 3）

#### 3.1 新增 Word Loader

**文件**：`src/libs/loader/word_loader.py`

**依赖**：
```bash
pip install python-docx
```

**实现要点**：
- 使用 `python-docx` 解析 `.docx` 文件
- 提取文本内容，转换为 Markdown 格式
- 提取元数据（标题、作者、创建时间）
- 支持表格转换为 Markdown 表格

**代码框架**：
```python
from docx import Document
from src.libs.loader.base_loader import BaseLoader
from src.core.types import Document

class WordLoader(BaseLoader):
    """Word document loader for .docx files."""

    def load(self, file_path: str | Path) -> Document:
        path = self._validate_file(file_path)
        doc = Document(str(path))

        # 提取文本
        text_parts = []
        for para in doc.paragraphs:
            text_parts.append(para.text)

        # 提取表格
        for table in doc.tables:
            text_parts.append(self._table_to_markdown(table))

        # 提取元数据
        metadata = {
            "source_path": str(path),
            "file_type": "docx",
            "title": doc.core_properties.title or path.stem,
            "author": doc.core_properties.author,
        }

        return Document(text="\n\n".join(text_parts), metadata=metadata)

    def _table_to_markdown(self, table) -> str:
        # 将表格转换为 Markdown 格式
        ...
```

#### 3.2 新增 Markdown Loader

**文件**：`src/libs/loader/markdown_loader.py`

**实现要点**：
- 直接读取 `.md` 文件
- 提取 YAML frontmatter 作为元数据
- 保留原始 Markdown 内容

**代码框架**：
```python
import re
from src.libs.loader.base_loader import BaseLoader
from src.core.types import Document

class MarkdownLoader(BaseLoader):
    """Markdown document loader for .md files."""

    def load(self, file_path: str | Path) -> Document:
        path = self._validate_file(file_path)

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 frontmatter
        metadata = {"source_path": str(path), "file_type": "md"}
        text = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = self._parse_frontmatter(parts[1])
                metadata.update(frontmatter)
                text = parts[2].strip()

        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1)

        return Document(text=text, metadata=metadata)
```

#### 3.3 更新摄取脚本

**文件**：`scripts/ingest.py`

修改 `discover_files` 函数，支持多格式：

```python
def discover_files(path: str, extensions: List[str] = None) -> List[Path]:
    if extensions is None:
        extensions = ['.pdf', '.docx', '.md', '.txt']  # 扩展支持格式
    # ... 其余逻辑不变
```

---

### 阶段四：服务器部署（Day 4）

#### 4.1 创建 Dockerfile

**文件**：`Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据目录
RUN mkdir -p data/db/chroma logs

# 暴露端口（Dashboard）
EXPOSE 8501

# 默认启动 Dashboard
CMD ["python", "scripts/start_dashboard.py"]
```

#### 4.2 创建 Docker Compose

**文件**：`docker-compose.yml`

```yaml
version: '3.8'

services:
  rag-server:
    build: .
    container_name: enterprise-knowledge-hub
    ports:
      - "8501:8501"  # Dashboard
    volumes:
      - ./data:/app/data           # 数据持久化
      - ./config:/app/config       # 配置文件
      - ./logs:/app/logs           # 日志
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
      - GLM_API_KEY=${GLM_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped

  # 可选：Nginx 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - rag-server
```

#### 4.3 创建环境变量模板

**文件**：`.env.example`

```bash
# LLM Provider API Keys
DEEPSEEK_API_KEY=your-deepseek-api-key
QWEN_API_KEY=your-qwen-api-key
GLM_API_KEY=your-glm-api-key

# Embedding Provider
OPENAI_API_KEY=your-openai-api-key

# 可选：自定义配置
LOG_LEVEL=INFO
```

#### 4.4 部署脚本

**文件**：`deploy.sh`

```bash
#!/bin/bash

# 企业知识库部署脚本

echo "=== 企业知识库部署 ==="

# 1. 检查环境变量
if [ ! -f .env ]; then
    echo "错误: 请先创建 .env 文件（参考 .env.example）"
    exit 1
fi

# 2. 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 3. 启动服务
echo "启动服务..."
docker-compose up -d

# 4. 检查状态
echo "检查服务状态..."
docker-compose ps

echo "=== 部署完成 ==="
echo "Dashboard: http://localhost:8501"
echo "MCP Server: 通过 stdin/stdout 通信"
```

---

### 阶段五：配置模板（Day 4）

#### 5.1 DeepSeek 配置模板

**文件**：`config/settings.deepseek.yaml`

```yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  api_key: "${DEEPSEEK_API_KEY}"
  temperature: 0.0
  max_tokens: 4096

embedding:
  provider: "openai"
  model: "text-embedding-ada-002"
  api_key: "${OPENAI_API_KEY}"
  dimensions: 1536

# ... 其余配置同默认配置
```

#### 5.2 千问配置模板

**文件**：`config/settings.qwen.yaml`

```yaml
llm:
  provider: "qwen"
  model: "qwen-plus"
  api_key: "${QWEN_API_KEY}"
  temperature: 0.0
  max_tokens: 4096

embedding:
  provider: "qwen"
  model: "text-embedding-v2"
  api_key: "${QWEN_API_KEY}"
  dimensions: 1536

# ... 其余配置同默认配置
```

#### 5.3 GLM 配置模板

**文件**：`config/settings.glm.yaml`

```yaml
llm:
  provider: "glm"
  model: "glm-4"
  api_key: "${GLM_API_KEY}"
  temperature: 0.0
  max_tokens: 4096

embedding:
  provider: "openai"  # GLM 暂无 embedding API，使用 OpenAI
  model: "text-embedding-ada-002"
  api_key: "${OPENAI_API_KEY}"
  dimensions: 1536

# ... 其余配置同默认配置
```

---

## 四、文件清单

### 4.1 后端新增文件

#### FastAPI 应用

| 文件路径 | 说明 |
|----------|------|
| `app/main.py` | FastAPI 入口文件 |
| `app/api/deps.py` | 依赖注入 |
| `app/api/v1/router.py` | 路由汇总 |
| `app/api/v1/chat.py` | 问答接口 |
| `app/api/v1/documents.py` | 文档接口 |
| `app/api/v1/search.py` | 搜索接口 |
| `app/api/v1/stats.py` | 统计接口 |
| `app/api/v1/user.py` | 用户接口 |
| `app/schemas/chat.py` | 问答数据模型 |
| `app/schemas/document.py` | 文档数据模型 |
| `app/schemas/user.py` | 用户数据模型 |
| `app/schemas/common.py` | 通用数据模型 |
| `app/services/chat_service.py` | 问答业务逻辑 |
| `app/services/document_service.py` | 文档业务逻辑 |
| `app/services/search_service.py` | 搜索业务逻辑 |
| `app/services/user_service.py` | 用户业务逻辑 |
| `app/core/config.py` | 配置管理 |
| `scripts/start_api.py` | API 启动脚本 |

#### LLM Provider 扩展

| 文件路径 | 说明 |
|----------|------|
| `src/libs/llm/qwen_llm.py` | 千问 LLM Provider |
| `src/libs/llm/glm_llm.py` | GLM LLM Provider |
| `src/libs/embedding/qwen_embedding.py` | 千问 Embedding Provider |

#### 文档格式扩展

| 文件路径 | 说明 |
|----------|------|
| `src/libs/loader/word_loader.py` | Word 文档加载器 |
| `src/libs/loader/markdown_loader.py` | Markdown 文档加载器 |

### 4.2 前端新增文件

#### Vue 项目结构

| 文件路径 | 说明 |
|----------|------|
| `frontend/package.json` | 项目依赖配置 |
| `frontend/vite.config.ts` | Vite 构建配置 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/index.html` | HTML 入口 |
| `frontend/src/main.ts` | Vue 入口文件 |
| `frontend/src/App.vue` | 根组件 |
| `frontend/src/api/index.ts` | Axios 实例 |
| `frontend/src/api/chat.ts` | 问答 API |
| `frontend/src/api/document.ts` | 文档 API |
| `frontend/src/api/search.ts` | 搜索 API |
| `frontend/src/api/user.ts` | 用户 API |
| `frontend/src/components/common/AppHeader.vue` | 顶部导航 |
| `frontend/src/components/common/AppSidebar.vue` | 侧边栏 |
| `frontend/src/components/common/SearchBox.vue` | 搜索框 |
| `frontend/src/components/chat/ChatMessage.vue` | 对话消息 |
| `frontend/src/components/chat/ChatInput.vue` | 输入框 |
| `frontend/src/components/chat/SourceCard.vue` | 引用来源卡片 |
| `frontend/src/components/chat/RelatedQuestions.vue` | 相关问题 |
| `frontend/src/components/document/DocCard.vue` | 文档卡片 |
| `frontend/src/components/document/CategoryTree.vue` | 分类树 |
| `frontend/src/views/HomeView.vue` | 首页 |
| `frontend/src/views/ChatView.vue` | 智能问答 |
| `frontend/src/views/DocumentsView.vue` | 文档中心 |
| `frontend/src/views/DocumentDetailView.vue` | 文档详情 |
| `frontend/src/views/ProfileView.vue` | 个人中心 |
| `frontend/src/stores/chat.ts` | 对话状态 |
| `frontend/src/stores/document.ts` | 文档状态 |
| `frontend/src/stores/user.ts` | 用户状态 |
| `frontend/src/router/index.ts` | 路由配置 |
| `frontend/src/styles/variables.scss` | 样式变量 |
| `frontend/src/styles/global.scss` | 全局样式 |

### 4.3 部署配置文件

| 文件路径 | 说明 |
|----------|------|
| `Dockerfile.backend` | 后端 Docker 镜像 |
| `Dockerfile.frontend` | 前端 Docker 镜像 |
| `docker-compose.yml` | 容器编排 |
| `nginx.conf` | Nginx 配置 |
| `.env.example` | 环境变量模板 |
| `deploy.sh` | 部署脚本 |
| `config/settings.deepseek.yaml` | DeepSeek 配置 |
| `config/settings.qwen.yaml` | 千问配置 |
| `config/settings.glm.yaml` | GLM 配置 |

### 4.4 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `src/libs/llm/__init__.py` | 注册新 LLM Provider |
| `src/libs/embedding/__init__.py` | 注册新 Embedding Provider |
| `scripts/ingest.py` | 支持多格式文档 |
| `requirements.txt` | 添加 FastAPI、python-docx 依赖 |

---

## 五、时间规划

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 阶段一 | 环境配置与基础测试 | Day 1 |
| 阶段二 | 扩展 LLM Provider | Day 2 |
| 阶段三 | 扩展文档格式 | Day 3 |
| **阶段四** | **FastAPI 后端开发** | **Day 4-5** |
| **阶段五** | **Vue.js 前端开发** | **Day 6-8** |
| 阶段六 | 服务器部署 | Day 9 |

**总计：9 个工作日**

### 详细时间分配

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 1 | DeepSeek 配置、PDF 测试 | 基础功能可用 |
| Day 2 | 千问/GLM Provider | 多 LLM 支持 |
| Day 3 | Word/Markdown Loader | 多格式支持 |
| Day 4 | FastAPI 项目搭建、API 设计 | 后端框架就绪 |
| Day 5 | 问答、文档、搜索接口 | 后端 API 完成 |
| Day 6 | Vue 项目搭建、通用组件 | 前端框架就绪 |
| Day 7 | 首页、智能问答页面 | 核心页面完成 |
| Day 8 | 文档中心、个人中心 | 前端全部完成 |
| Day 9 | Docker 部署、联调测试 | 可交付系统 |

---

## 六、验收标准

### 6.1 功能验收

#### 后端能力

- [ ] DeepSeek LLM 正常调用
- [ ] 千问 LLM 正常调用
- [ ] GLM LLM 正常调用
- [ ] PDF 文档正常摄取
- [ ] Word 文档正常摄取
- [ ] Markdown 文档正常摄取
- [ ] 混合检索正常工作
- [ ] MCP Server 正常启动

#### 前端界面

- [ ] 知识库前台可正常访问
- [ ] 首页搜索框可用
- [ ] 智能问答功能正常
- [ ] 问答结果展示引用来源
- [ ] 文档中心可浏览文档
- [ ] 文档分类筛选正常
- [ ] 个人中心显示查询历史
- [ ] 管理后台（现有）正常访问

### 6.2 部署验收

- [ ] Docker 镜像构建成功
- [ ] Docker Compose 启动成功
- [ ] 知识库前台可通过浏览器访问（端口 8501）
- [ ] 管理后台可通过浏览器访问（端口 8502）
- [ ] 数据持久化正常
- [ ] 日志正常输出

---

## 七、部署架构

### 7.1 部署架构图

```
                    ┌─────────────────────────────────────┐
                    │           Nginx (80/443)            │
                    │         反向代理 + 静态资源          │
                    └───────────────┬─────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │   Vue 前端         │           │   FastAPI 后端     │
        │   (静态文件)       │           │   (端口: 8000)     │
        │                   │           │                   │
        │   / → index.html  │           │   /api/v1/*       │
        │   /chat → index   │           │   /health         │
        │   /documents → ...│           │   /docs (Swagger) │
        └───────────────────┘           └─────────┬─────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
        ┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
        │   ChromaDB        │         │   BM25 Index      │         │   文件存储         │
        │   (向量数据库)     │         │   (稀疏索引)       │         │   (文档/图片)      │
        └───────────────────┘         └───────────────────┘         └───────────────────┘
```

### 7.2 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: unless-stopped

  # FastAPI 后端
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
      - GLM_API_KEY=${GLM_API_KEY}
    restart: unless-stopped

  # 现有 Streamlit 管理后台（可选）
  admin-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8502:8501"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    profiles:
      - admin  # 可选启动
    restart: unless-stopped
```

### 7.3 Nginx 配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;  # Vue Router history 模式
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # SSE 流式响应支持
            proxy_buffering off;
            proxy_cache off;
        }

        # 健康检查
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
```

### 7.4 Dockerfile

**后端 Dockerfile:**

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY app/ ./app/
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# 创建目录
RUN mkdir -p data/db/chroma logs

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile:**

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 7.5 环境变量

```bash
# .env.example

# LLM Provider API Keys
DEEPSEEK_API_KEY=your-deepseek-api-key
QWEN_API_KEY=your-qwen-api-key
GLM_API_KEY=your-glm-api-key
OPENAI_API_KEY=your-openai-api-key

# 应用配置
APP_ENV=production
LOG_LEVEL=INFO

# 数据库路径
CHROMA_PERSIST_DIR=./data/db/chroma
```

1. **性能优化**
   - 批量摄取优化
   - 检索缓存
   - 并发查询

2. **功能扩展**
   - 权限控制（如需要）
   - 文档版本管理
   - 检索历史记录
   - 知识图谱

3. **运维增强**
   - 监控告警
   - 自动备份
   - 日志收集

---

## 九、后续优化方向

1. **性能优化**
   - 批量摄取优化
   - 检索缓存
   - 并发查询

2. **功能扩展**
   - 权限控制（如需要）
   - 文档版本管理
   - 检索历史记录
   - 知识图谱

3. **运维增强**
   - 监控告警
   - 自动备份
   - 日志收集

---

## 十、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| API 限流 | 摄取速度受限 | 实现限流控制，分批摄取 |
| 文档格式复杂 | 解析失败 | 增加容错处理，记录失败文档 |
| 内存不足 | 大文档处理失败 | 分块处理，流式读取 |
| 网络不稳定 | API 调用失败 | 实现重试机制 |

---

**文档版本**：v1.0
**创建日期**：2026-03-28
**作者**：Claude Code
