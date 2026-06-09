# 柜子家具3D编辑器 — 软件规格说明书 (SPEC)

## 1. 项目概述

### 1.1 项目名称
**CabinetCraft** — 智能柜子家具3D在线编辑器

### 1.2 项目目标
构建一个在线3D柜子编辑平台，用户既可以通过可视化编辑面板对柜子进行增删改操作，也可以通过自然语言指令让AI自动完成编辑，降低柜子定制设计门槛。

### 1.3 核心价值
- **双通道编辑**：可视化面板 + 自然语言，灵活适配不同用户习惯
- **实时3D预览**：基于Three.js的WebGL渲染，所见即所得
- **AI驱动**：LLM理解用户意图，自动转化为3D操作

---

## 2. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue 3 + TypeScript | 组件化开发，类型安全 |
| 构建工具 | Vite | 快速HMR，ESBuild打包 |
| 3D渲染 | Three.js | WebGL 3D渲染引擎 |
| 后端框架 | FastAPI (Python 3.10+) | 异步高性能API |
| AI Agent | DeepAgents | LLM Agent编排与工具调用 |
| 数据库 | SQLite + SQLAlchemy | 轻量级持久化存储 |
| LLM | OpenAI API / 兼容接口 | 自然语言理解与生成 |

---

## 3. 功能需求

### 3.1 可视化编辑面板 (Panel Editor)

#### 3.1.1 柜子查看
- **3D场景渲染**：基于Three.js渲染柜子3D模型，支持旋转/缩放/平移视角
- **网格/轴线辅助**：可开关的地面网格和坐标轴，辅助空间定位
- **柜子信息展示**：选中柜子后高亮显示，面板展示尺寸、材质、颜色等属性

#### 3.1.2 柜子增删改
- **新增柜子**：
  - 从预设模板库选择柜子类型（底柜、吊柜、高柜、角柜等）
  - 放置到场景中，支持拖拽调整位置
- **删除柜子**：
  - 选中柜子后通过面板按钮或键盘Delete键删除
  - 删除前确认提示
- **修改柜子**：
  - 尺寸调整：宽度、高度、深度（带滑块和数值输入）
  - 位置调整：X/Y/Z坐标（支持拖拽和数值输入）
  - 旋转调整：绕Y轴旋转角度
  - 材质/颜色切换：预设材质库（木纹、烤漆、金属等）
  - 门板样式：平板门、造型门、玻璃门
  - 把手样式：隐藏把手、长条把手、圆钮把手

#### 3.1.3 场景管理
- **撤销/重做**：支持操作历史回退和前进（Ctrl+Z / Ctrl+Y）
- **重置场景**：清空所有柜子回到初始状态
- **保存/加载**：保存当前设计到数据库，支持从历史记录加载

### 3.2 自然语言编辑 (AI Editor)

#### 3.2.1 对话式编辑
- **聊天面板**：侧边栏或底部面板提供聊天输入框
- **意图理解**：LLM解析用户自然语言，识别以下操作意图：
  - 增加柜子："加一个宽800高700深600的底柜"
  - 删除柜子："把第二个柜子删掉"
  - 修改属性："把第一个柜子的颜色改成白色烤漆"
  - 移动柜子："把吊柜往右边移20厘米"
  - 批量操作："给所有底柜换成木纹材质"
  - 查询信息："当前有几个柜子？最大的是哪个？"
- **操作确认**：AI生成的操作计划在执行前展示给用户确认
- **反馈提示**：操作执行成功后更新3D视图并给出文字反馈

#### 3.2.2 Agent工具链
DeepAgents Agent具备以下工具（函数调用）：

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `add_cabinet` | 新增柜子 | type, width, height, depth, position_x, position_y, position_z, color, material |
| `remove_cabinet` | 删除柜子 | cabinet_id |
| `update_cabinet` | 修改柜子属性 | cabinet_id, 任意修改字段 |
| `move_cabinet` | 移动柜子 | cabinet_id, delta_x, delta_y, delta_z |
| `list_cabinets` | 列出所有柜子 | 无 |
| `get_cabinet` | 获取单个柜子详情 | cabinet_id |
| `clear_scene` | 清空场景 | 无 |
| `undo` / `redo` | 撤销/重做 | 无 |
| `get_scene_snapshot` | 获取当前场景快照描述 | 无（供LLM理解当前状态） |

---

## 4. 系统架构

### 4.1 整体架构图

```
┌─────────────────────────────────────────────────┐
│                    前端 (Vue 3)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 3D View  │ │  Panel   │ │   Chat Panel     │ │
│  │(Three.js)│ │ Editor   │ │  (AI Dialog)     │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│       │            │               │            │
│       └────────────┼───────────────┘            │
│                    │  HTTP/SSE                   │
└────────────────────┼────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────┐
│              后端 (FastAPI)                       │
│  ┌─────────────────┴──────────────────┐          │
│  │          API Router                 │          │
│  │  /api/cabinets    CRUD操作          │          │
│  │  /api/scene       场景管理          │          │
│  │  /api/ai          AI对话(SSE)       │          │
│  └────────┬───────────────────────────┘          │
│           │                                      │
│  ┌────────┴──────────┐  ┌───────────────────┐   │
│  │  CabinetService   │  │   DeepAgents       │   │
│  │  (业务逻辑)       │  │   Agent + Tools    │   │
│  └────────┬──────────┘  └─────────┬─────────┘   │
│           │                       │              │
│  ┌────────┴───────────────────────┴──────────┐   │
│  │          SQLAlchemy ORM / SQLite           │   │
│  └────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────┘
```

### 4.2 数据流

```
用户操作 → Vue组件 → API请求 → FastAPI路由
    → CabinetService(业务处理) → SQLite持久化
    → 返回结果 → Vue更新状态 → Three.js重新渲染

AI对话 → Vue聊天组件 → POST /api/ai/chat(SSE流式)
    → DeepAgents Agent(理解意图→工具调用→生成回复)
    → SSE事件流 → Vue实时展示 → 3D场景刷新
```

---

## 5. 数据库设计

### 5.1 ER图说明
共3张核心表：`cabinets`、`scenes`、`chat_history`

### 5.2 表结构

#### cabinets（柜子表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 柜子唯一ID |
| scene_id | INTEGER | FK → scenes.id, NOT NULL | 所属场景 |
| cabinet_type | VARCHAR(32) | NOT NULL | 类型：base(底柜)/wall(吊柜)/tall(高柜)/corner(角柜) |
| name | VARCHAR(64) | DEFAULT '' | 柜子名称/标签 |
| width | FLOAT | NOT NULL, DEFAULT 600 | 宽度(mm) |
| height | FLOAT | NOT NULL, DEFAULT 700 | 高度(mm) |
| depth | FLOAT | NOT NULL, DEFAULT 500 | 深度(mm) |
| position_x | FLOAT | NOT NULL, DEFAULT 0 | X坐标 |
| position_y | FLOAT | NOT NULL, DEFAULT 0 | Y坐标(高度) |
| position_z | FLOAT | NOT NULL, DEFAULT 0 | Z坐标 |
| rotation_y | FLOAT | NOT NULL, DEFAULT 0 | 绕Y轴旋转(弧度) |
| color | VARCHAR(32) | DEFAULT '#FFFFFF' | 颜色(hex) |
| material | VARCHAR(32) | DEFAULT 'wood' | 材质：wood/paint/metal/glass |
| door_style | VARCHAR(32) | DEFAULT 'flat' | 门板：flat(平板)/panel(造型)/glass(玻璃) |
| handle_style | VARCHAR(32) | DEFAULT 'hidden' | 把手：hidden/long/knob |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### scenes（场景表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 场景ID |
| name | VARCHAR(128) | NOT NULL | 场景名称 |
| description | TEXT | DEFAULT '' | 场景描述 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### chat_history（对话历史表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 消息ID |
| scene_id | INTEGER | FK → scenes.id, NOT NULL | 所属场景 |
| role | VARCHAR(16) | NOT NULL | 角色：user/assistant/system |
| content | TEXT | NOT NULL | 消息内容 |
| tool_calls | TEXT | DEFAULT NULL | JSON格式的工具调用记录 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 6. API 接口设计

### 6.1 柜子CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scenes/{scene_id}/cabinets` | 获取场景所有柜子 |
| GET | `/api/scenes/{scene_id}/cabinets/{cabinet_id}` | 获取单个柜子 |
| POST | `/api/scenes/{scene_id}/cabinets` | 新增柜子 |
| PUT | `/api/scenes/{scene_id}/cabinets/{cabinet_id}` | 更新柜子 |
| DELETE | `/api/scenes/{scene_id}/cabinets/{cabinet_id}` | 删除柜子 |

### 6.2 场景管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scenes` | 列出所有场景 |
| POST | `/api/scenes` | 创建新场景 |
| GET | `/api/scenes/{scene_id}` | 获取场景详情 |
| PUT | `/api/scenes/{scene_id}` | 更新场景信息 |
| DELETE | `/api/scenes/{scene_id}` | 删除场景 |

### 6.3 AI对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | 发送自然语言指令（SSE流式响应） |

**POST /api/ai/chat 请求体：**

```json
{
  "scene_id": 1,
  "message": "加一个宽800高700深600的白色底柜",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**SSE事件流格式：**

```
event: thinking
data: {"content": "正在分析你的需求..."}

event: tool_call
data: {"tool": "add_cabinet", "args": {...}}

event: message
data: {"content": "已添加一个宽800mm、高700mm、深600mm的白色底柜。"}

event: done
data: {"scene_id": 1, "cabinet_count": 3}
```

### 6.4 撤销/重做

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/scenes/{scene_id}/undo` | 撤销上一步操作 |
| POST | `/api/scenes/{scene_id}/redo` | 重做已撤销操作 |

### 6.5 响应格式

所有API统一响应格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

错误时：

```json
{
  "success": false,
  "data": null,
  "error": {"code": "CABINET_NOT_FOUND", "message": "柜子不存在"}
}
```

---

## 7. 前端设计

### 7.1 页面布局

```
┌──────────────────────────────────────────────────┐
│  Header: Logo | 场景名称 | 保存 | 加载 | 撤销/重做 │
├─────────────────────┬────────────────────────────┤
│                     │                            │
│   3D 视图区域        │    右侧面板 (320px)         │
│   (Three.js         │  ┌──────────────────────┐  │
│    Canvas)          │  │ 属性编辑 / AI对话     │  │
│                     │  │  Tab切换             │  │
│                     │  ├──────────────────────┤  │
│                     │  │                      │  │
│                     │  │  - 柜子列表           │  │
│                     │  │  - 尺寸编辑           │  │
│                     │  │  - 位置编辑           │  │
│                     │  │  - 材质/颜色          │  │
│                     │  │  - AI对话面板         │  │
│                     │  │                      │  │
│                     │  └──────────────────────┘  │
│                     │                            │
└─────────────────────┴────────────────────────────┘
```

### 7.2 组件树

```
App.vue
├── AppHeader.vue              # 顶部导航栏
│   ├── SceneSelector.vue      # 场景选择器
│   └── ActionButtons.vue      # 保存/加载/撤销/重做按钮
├── MainLayout.vue             # 主体布局
│   ├── ThreeCanvas.vue        # 3D渲染画布（核心）
│   │   ├── CabinetMesh.vue    # 单个柜子Mesh（程序化生成）
│   │   ├── GridHelper.vue     # 地面网格
│   │   ├── OrbitControls      # 视角控制（Three.js内置）
│   │   └── TransformControls  # 拖拽变换控制
│   └── RightPanel.vue         # 右侧面板
│       ├── PropertyEditor.vue # 属性编辑器
│       │   ├── CabinetList.vue    # 柜子列表
│       │   ├── SizeEditor.vue     # 尺寸编辑
│       │   ├── PositionEditor.vue # 位置编辑
│       │   └── StyleEditor.vue    # 样式编辑（颜色/材质/门板/把手）
│       └── AIChatPanel.vue    # AI对话面板
│           ├── ChatMessages.vue   # 消息列表
│           └── ChatInput.vue      # 输入框
└── ConfirmDialog.vue          # 确认对话框
```

### 7.3 核心状态管理 (Pinia Store)

```typescript
// stores/scene.ts
interface SceneStore {
  currentScene: Scene | null;
  cabinets: Cabinet[];
  selectedCabinetId: number | null;
  undoStack: Snapshot[];      // 用于前端撤销缓存
  redoStack: Snapshot[];
}

// stores/chat.ts
interface ChatStore {
  messages: ChatMessage[];
  isStreaming: boolean;
}
```

### 7.4 Three.js 渲染核心

- **柜子建模**：使用 `BoxGeometry` 构建柜体，程序化添加门板、把手等细节
- **材质系统**：预设颜色/纹理的 `MeshStandardMaterial`
- **选中高亮**：`OutlinePass` 或边缘发光效果
- **光照**：环境光 + 方向光 + 半球光，模拟室内光照
- **阴影**：`ShadowMap` 提升真实感
- **射线检测**：`Raycaster` 实现点击选中柜子
- **变换控件**：`TransformControls` 实现拖拽移动/旋转
- **地面参考**：`GridHelper` 提供空间参考

---

## 8. 后端设计

### 8.1 项目结构

```
backend/
├── main.py                  # FastAPI入口
├── config.py                # 配置（数据库路径、LLM Key等）
├── database.py              # SQLAlchemy初始化
├── models/
│   ├── __init__.py
│   ├── cabinet.py           # Cabinet ORM模型
│   ├── scene.py             # Scene ORM模型
│   └── chat.py              # ChatHistory ORM模型
├── schemas/
│   ├── __init__.py
│   ├── cabinet.py           # Pydantic请求/响应模型
│   ├── scene.py
│   └── chat.py
├── routers/
│   ├── __init__.py
│   ├── cabinets.py          # 柜子CRUD路由
│   ├── scenes.py            # 场景路由
│   └── ai.py                # AI对话路由（SSE）
├── services/
│   ├── __init__.py
│   ├── cabinet_service.py   # 柜子业务逻辑
│   ├── scene_service.py     # 场景业务逻辑
│   └── undo_service.py      # 撤销/重做管理
├── agent/
│   ├── __init__.py
│   ├── agent.py             # DeepAgents Agent定义
│   └── tools.py             # Agent工具函数定义
└── tests/
    ├── __init__.py
    ├── test_cabinets.py
    ├── test_scenes.py
    └── test_ai.py
```

### 8.2 CabinetService 核心方法

```python
class CabinetService:
    def list_cabinets(self, scene_id: int) -> list[Cabinet]
    def get_cabinet(self, cabinet_id: int) -> Cabinet
    def create_cabinet(self, scene_id: int, data: CabinetCreate) -> Cabinet
    def update_cabinet(self, cabinet_id: int, data: CabinetUpdate) -> Cabinet
    def delete_cabinet(self, cabinet_id: int) -> None
    def get_scene_snapshot(self, scene_id: int) -> str  # 生成场景文本描述供LLM理解
```

### 8.3 UndoService 实现思路

- 每次对柜子的增删改操作前，保存当前场景状态快照到 `undo_stack`
- 撤销时恢复上一个快照；重做时恢复下一个快照
- 快照存储策略：按 `scene_id` 隔离，每个场景维护独立的undo/redo栈
- 实现方式：在数据库中记录操作版本，或使用JSON快照序列化

### 8.4 DeepAgents Agent 设计

```python
# agent/agent.py
from deepagents import Agent, tool
from services.cabinet_service import CabinetService

class CabinetEditorAgent:
    def __init__(self, llm_client, tools: list[tool]):
        self.agent = Agent(
            model=llm_client,
            tools=tools,
            system_prompt="""
你是一个柜子家具3D编辑助手。用户会用自然语言描述想要对柜子进行的操作。
你需要：
1. 理解用户意图
2. 调用合适的工具函数完成操作
3. 用简洁友好的中文回复用户

可用的柜子类型：base(底柜), wall(吊柜), tall(高柜), corner(角柜)
尺寸单位：毫米(mm)

如果用户没有指定某些参数，使用合理的默认值。
在执行操作前，如果场景中有多个柜子，先调用list_cabinets了解当前状态。
            """
        )

    async def chat(self, scene_id: int, message: str, history: list) -> AsyncGenerator:
        """生成SSE事件流"""
```

### 8.5 Agent 工具定义示例

```python
# agent/tools.py
@tool
async def add_cabinet(
    scene_id: int,
    cabinet_type: str = "base",
    width: float = 600,
    height: float = 700,
    depth: float = 500,
    position_x: float = 0,
    position_y: float = 0,
    position_z: float = 0,
    color: str = "#FFFFFF",
    material: str = "wood"
) -> str:
    """新增一个柜子到场景中"""
    # 调用CabinetService
    ...

@tool
async def remove_cabinet(scene_id: int, cabinet_id: int) -> str:
    """从场景中删除指定柜子"""
    ...

@tool
async def list_cabinets(scene_id: int) -> str:
    """列出场景中所有柜子及其属性"""
    ...
```

---

## 9. 交互流程

### 9.1 可视化编辑流程

```
用户进入页面
  → 加载/创建场景
  → GET /api/scenes/{id}/cabinets 获取柜子列表
  → Three.js渲染所有柜子

用户点击"添加柜子"按钮
  → 弹出类型选择（底柜/吊柜/高柜/角柜）
  → POST /api/scenes/{id}/cabinets 创建柜子
  → Three.js场景新增一个Mesh
  → 自动选中新柜子

用户选中柜子
  → 高亮显示
  → 右侧面板显示属性
  → 修改属性 → PUT /api/scenes/{id}/cabinets/{cid}
  → Three.js更新对应Mesh

用户拖拽柜子
  → TransformControls实时更新位置
  → 松手后 PUT 同步到后端

用户删除柜子
  → 确认对话框
  → DELETE /api/scenes/{id}/cabinets/{cid}
  → Three.js移除对应Mesh
```

### 9.2 AI对话编辑流程

```
用户在AI面板输入: "加一个白色烤漆底柜，宽80厘米"
  → POST /api/ai/chat (SSE)

后端:
  → 加载对话历史
  → DeepAgents Agent分析意图
  → SSE: thinking事件 → "正在理解你的需求..."
  → Agent调用 add_cabinet(type="base", width=800, color="#FFFFFF", material="paint")
  → SSE: tool_call事件 → 展示将要执行的操作
  → 执行成功
  → SSE: message事件 → "已添加一个宽800mm的白色烤漆底柜"
  → SSE: done事件

前端:
  → 接收SSE事件流
  → 实时展示思考过程
  → 收到done后刷新柜子列表
  → Three.js渲染新柜子
```

---

## 10. 错误处理

### 10.1 后端错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| SCENE_NOT_FOUND | 404 | 场景不存在 |
| CABINET_NOT_FOUND | 404 | 柜子不存在 |
| INVALID_PARAMS | 400 | 参数校验失败 |
| AI_ERROR | 500 | AI服务调用失败 |
| UNDO_NOT_AVAILABLE | 400 | 无可撤销操作 |
| REDO_NOT_AVAILABLE | 400 | 无可重做操作 |

### 10.2 前端错误处理

- API调用失败时：Toast提示错误信息
- AI流式响应中断：提示用户重试
- 3D渲染异常：显示降级提示

---

## 11. 测试策略

### 11.1 后端测试（pytest）

| 测试模块 | 测试内容 |
|----------|----------|
| `test_cabinets.py` | 柜子CRUD接口测试：创建/查询/更新/删除，参数校验 |
| `test_scenes.py` | 场景管理接口测试：创建/列表/更新/删除 |
| `test_ai.py` | AI对话接口测试：Mock LLM响应，验证SSE输出格式，验证工具调用逻辑 |
| `test_undo.py` | 撤销/重做逻辑测试 |
| `test_agent_tools.py` | Agent工具函数单元测试 |

### 11.2 前端测试（Vitest + Vue Test Utils）

| 测试模块 | 测试内容 |
|----------|----------|
| 组件渲染测试 | 各组件能否正常挂载渲染 |
| Store测试 | Pinia Store状态变更逻辑 |
| API Mock测试 | Mock后端接口，验证组件交互行为 |

### 11.3 E2E测试（Playwright 可选）

- 完整用户流程：打开页面 → 创建场景 → 添加柜子 → 修改属性 → 删除柜子
- AI对话流程：输入指令 → 验证SSE响应 → 验证3D场景变化

---

## 12. 开发环境与运行

### 12.1 前端

```bash
cd frontend
npm install
npm run dev        # 开发模式，默认 http://localhost:5173
npm run build      # 生产构建
npm run test       # 运行测试
```

### 12.2 后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload    # 开发模式，默认 http://localhost:8000
pytest                       # 运行测试
```

### 12.3 环境变量

```
OPENAI_API_KEY=sk-xxx          # LLM API Key
OPENAI_BASE_URL=https://...    # LLM API Base URL（可选）
DATABASE_URL=sqlite:///./cabinet_craft.db
```

---

## 13. 版本规划

### V1.0 — MVP (本次实现)
- 基础柜子增删改（4种类型）
- 3D场景渲染与交互
- 简单AI对话编辑
- 撤销/重做
- 场景保存/加载

### V1.1 — 增强（后续迭代）
- 更多柜子模板（抽屉柜、开放格等）
- 柜体组合/分组
- 材质纹理上传
- 导出设计图（截图/PDF）
- 多场景管理
- 柜子碰撞检测

---

## 附录 A：柜子尺寸默认值参考

| 类型 | 默认宽度 | 默认高度 | 默认深度 |
|------|---------|---------|---------|
| 底柜(base) | 600mm | 700mm | 500mm |
| 吊柜(wall) | 600mm | 600mm | 350mm |
| 高柜(tall) | 600mm | 2000mm | 500mm |
| 角柜(corner) | 900mm | 700mm | 900mm×900mm(L型) |

## 附录 B：材质预设

| 材质标识 | 显示名称 | 颜色范围 | 说明 |
|----------|----------|----------|------|
| wood_oak | 橡木 | #C49A6C | 浅棕色木纹 |
| wood_walnut | 胡桃木 | #6B4226 | 深棕色木纹 |
| paint_white | 白色烤漆 | #F5F5F5 | 光滑白色 |
| paint_black | 黑色烤漆 | #2C2C2C | 光滑黑色 |
| paint_grey | 灰色烤漆 | #A0A0A0 | 中性灰 |
| metal_steel | 不锈钢 | #C0C0C0 | 金属拉丝 |
| glass_clear | 透明玻璃 | rgba(200,220,255,0.3) | 半透明 |