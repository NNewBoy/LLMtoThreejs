# AGENTS.md — Agent + Skills 架构文档

本文档面向开发者，详细说明 CabinetCraft Pro 的 LLM Agent + Skills 架构设计，包括如何理解、调试和扩展 AI 编辑能力。

## 架构总览

```
用户自然语言输入
       │
       ▼
┌──────────────────────┐
│   AIService          │  ← 会话管理、上下文构建
│   (services/ai_service.py)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   CabinetAgent       │  ← LLM 意图分析 + Skill 路由
│   (agent/agent.py)
│                      │
│   ┌────────────────┐ │
│   │ OpenAI SDK     │ │  ← Function Calling
│   │ (async)        │ │
│   └────────┬───────┘ │
│            │         │
│   ┌────────▼───────┐ │
│   │ SkillRegistry  │ │  ← Skill 注册 + Schema 生成
│   │ (agent/skill_registry.py)
│   └────────┬───────┘ │
└─────────────┼────────┘
              │
              ▼
┌──────────────────────┐
│   Skills 层           │  ← 领域操作封装
│   (skills/)
│                      │
│   ┌────────────────┐ │
│   │ ShelfSkill     │ │  add_shelf
│   │ DoorSkill      │ │  add_doors
│   │ DrawerSkill    │ │  add_drawers
│   │ MaterialSkill  │ │  change_material
│   │ QuerySkill     │ │  query_structure
│   │ ResizeSkill    │ │  adjust_cabinet_size
│   │ LayoutSkill    │ │  reorganize_layout
│   └────────┬───────┘ │
└─────────────┼────────┘
              │
              ▼
┌──────────────────────┐
│   Tools 层            │  ← 原子数据库操作
│   (agent/tools.py)
│                      │
│   add_component      │
│   remove_component   │
│   update_component   │
│   get_cabinet_structure
│   get_component      │
│   list_components    │
│   update_cabinet_size│
│   get_snapshot_description
└──────────────────────┘
```

## 数据流

### 1. 用户发送消息

```
POST /api/ai/chat
{
  "cabinet_id": 1,
  "message": "在柜子中间加两块隔板",
  "history": [...]
}
```

### 2. AIService 构建上下文

- 从数据库读取柜子当前状态
- 生成结构化描述（尺寸、组件列表、材质）
- 保存用户消息到 `ai_chat_history` 表

### 3. CabinetAgent 调用 LLM

- System Prompt 注入 Skills 描述 + 柜子坐标系说明
- 将 Skills 转换为 OpenAI Function Calling schema
- LLM 选择 Skill 并生成参数

### 4. Skill 执行

- Skill 接收参数，调用 Tools 层操作数据库
- 返回 `SkillResult(success, message, operations)`
- operations 是前端可执行的操作指令序列

### 5. SSE 事件流返回前端

```
event: thinking
data: {"content": "正在分析你的需求..."}

event: skill_selected
data: {"skill_id": "add_shelf", "skill_name": "添加隔板", "reasoning": "..."}

event: tool_calls
data: {"calls": [{"tool": "add_shelf", "args": {...}}]}

event: skill_completed
data: {"skill_id": "add_shelf", "result": "已添加 2 块隔板", "success": true}

event: message
data: {"content": "已完成：添加2块隔板（间距均匀分布）。"}

event: done
data: {"cabinet_id": 1, "operations": [...], "skills_used": ["add_shelf"]}
```

## 核心组件详解

### SkillRegistry（agent/skill_registry.py）

Skill 注册中心，负责：

1. **注册 Skill**：`registry.register(ShelfSkill(tools))`
2. **生成 LLM Schema**：将每个 Skill 转换为 OpenAI function 定义
3. **生成 Prompt 描述**：注入到 System Prompt 供 LLM 理解
4. **兜底匹配**：当 LLM 不可用时，用关键词匹配 Skill

```python
# 生成的 OpenAI Function Schema 示例
{
    "type": "function",
    "function": {
        "name": "add_shelf",
        "description": "在柜体内部指定位置添加活动隔板...",
        "parameters": {
            "type": "object",
            "properties": {
                "cabinet_id": {"type": "integer"},
                "params": {"type": "object"}
            },
            "required": ["cabinet_id", "params"]
        }
    }
}
```

### BaseSkill（skills/base.py）

所有 Skill 的抽象基类：

```python
class BaseSkill(ABC):
    skill_id: str          # 唯一标识，如 "add_shelf"
    skill_name: str        # 中文名称，如 "添加隔板"
    description: str       # 功能描述（给 LLM 做意图匹配）
    examples: list[str]    # 触发示例（给 LLM 理解用法）

    def can_handle(self, intent: str, context: dict) -> bool:
        """关键词兜底匹配"""

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        """执行 Skill，返回操作指令序列"""

    async def pre_check(self, cabinet_id: int, params: dict) -> bool:
        """执行前校验（可选）"""

    async def post_check(self, cabinet_id: int, result: SkillResult) -> bool:
        """执行后校验（可选）"""

    async def rollback(self, cabinet_id: int, params: dict) -> None:
        """回滚操作（可选）"""
```

### SkillResult（skills/base.py）

```python
@dataclass
class SkillResult:
    success: bool           # 是否成功
    message: str            # 用户可读的执行描述
    operations: list[dict]  # 返回给前端的操作指令序列
    error: Optional[str]    # 错误码（可选）
```

### Tools 层（agent/tools.py）

8 个原子操作函数，被 Skills 调用：

| 函数 | 说明 | 返回 |
|------|------|------|
| `add_component(db, **kw)` | 添加板件 | 新板件 dict |
| `remove_component(db, cabinet_id, component_id)` | 删除板件 | 删除操作 dict |
| `update_component(db, cabinet_id, component_id, **fields)` | 更新板件 | 更新后 dict |
| `get_cabinet_structure(db, cabinet_id)` | 获取柜子完整结构 | 含所有板件的 dict |
| `get_component(db, cabinet_id, component_id)` | 获取单个板件 | 板件 dict |
| `list_components(db, cabinet_id, component_type?)` | 列出板件 | 板件 dict 列表 |
| `update_cabinet_size(db, cabinet_id, w, h, d)` | 调整柜体尺寸 | 更新操作 dict |
| `get_snapshot_description(db, cabinet_id)` | 柜子文字描述 | 字符串 |

所有 Tools 都是普通 Python 函数（非 async，但被 Skill 包装为 async 调用）。Skill 通过 `self.tools` dict 调用它们。

## 各 Skill 详解

### ShelfSkill（add_shelf）

**参数：**
- `count`: 隔板数量（默认 1）
- `position_ratios`: 0~1 相对高度列表（如 `[0.33, 0.67]`）
- `material`, `color`: 可选材质/颜色

**领域规则：**
- 最小隔板间距 150mm
- 隔板宽度 = 柜体内部宽度
- 隔板深度 = 柜体内部深度
- 默认厚度 18mm

**行为：**
- 不指定 `position_ratios` 时自动均匀分布
- 碰撞检测：跳过与已有隔板距离 < 150mm 的位置

### DoorSkill（add_doors）

**参数：**
- `count`: 门板数量
- `style`: `flat` | `panel` | `glass` | `louver`
- `cover_range`: `full` | `upper` | `lower`
- `handle_style`: `hidden` | `long` | `knob`
- `material`, `color`: 可选

**领域规则：**
- 门缝 3mm
- 门板位于柜体前方 (Z = depth/2 + thickness/2)
- 删除旧门板时自动删除关联拉手
- 每扇门自动添加配套拉手

### DrawerSkill（add_drawers）

**参数：**
- `count`: 抽屉数量
- `start_ratio`, `end_ratio`: 0~1 起止相对高度
- `material`, `color`: 可选

**行为：**
- 抽屉宽度 = 柜体内部宽度
- 抽屉深度略小于内部深度（-20mm）
- 每个抽屉自动添加拉手

### MaterialSkill（change_material）

**参数：**
- `component_types`: 目标类型列表（如 `["shelf", "door"]`）
- `material`: 材质 ID
- `color`: 颜色值

**行为：**
- 不指定类型时应用到所有非必选板件
- 必选板件（顶/底/左/右板）默认跳过

### QuerySkill（query_structure）

**参数：** 无

**返回：** 人类可读的柜子结构描述，包含尺寸、组件统计、每块板件详情。

### ResizeSkill（adjust_cabinet_size）

**参数：**
- `width`, `height`, `depth`: 新尺寸（mm）

**行为：**
- 更新柜体尺寸
- 触发必选板件位置重新计算

### ReorganizeLayoutSkill（reorganize_layout）

**参数：**
- `layout_spec`: 布局描述 dict，包含 zones 列表

**行为：**
- 解析布局规格，编排子 Skills（DoorSkill、DrawerSkill、ShelfSkill）
- 支持"上面两门下面三抽屉"等复杂指令

## 如何添加新 Skill

### 1. 创建 Skill 文件

在 `backend/skills/` 下新建文件，如 `light_skill.py`：

```python
from skills.base import BaseSkill, SkillResult

class LightSkill(BaseSkill):
    skill_id = "add_light"
    skill_name = "添加灯光"
    description = "在柜子内部添加 LED 灯带"
    examples = ["加个灯", "柜子里装灯带"]

    def can_handle(self, intent: str, context: dict) -> bool:
        return any(kw in intent for kw in ["灯", "灯光", "LED", "light"])

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        add_component = self.tools["add_component"]

        cabinet = await get_structure(cabinet_id)
        # ... 计算灯光位置 ...
        op = await add_component(
            cabinet_id=cabinet_id,
            component_type="light",
            position_y=cabinet["height"] - 30,
            width=cabinet["width"] - 40,
            height=5,
            depth=10,
            label="LED灯带",
        )
        return SkillResult(
            success=True,
            message="已添加 LED 灯带",
            operations=[op],
        )
```

### 2. 注册 Skill

在 `backend/skills/__init__.py` 中添加：

```python
from skills.light_skill import LightSkill

ALL_SKILLS = [
    # ... 现有 skills ...
    LightSkill,
]
```

### 3. 更新前端类型（如需新组件类型）

在 `frontend/src/types/index.ts` 的 `ComponentType` 枚举中添加：

```typescript
Light = 'light',
```

在 `BoardFactory.ts` 中添加对应的默认位置和材质。

## 如何更换 LLM 提供商

编辑 `backend/.env`：

```env
# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o

# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=deepseek-chat

# 通义千问
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-...
LLM_MODEL=qwen-plus

# 本地 Ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5
```

任何支持 OpenAI Chat Completions API 格式的服务都可以接入。

## 调试技巧

### 查看 Agent 对话

在 `backend/agent/agent.py` 中设置日志级别：

```python
import logging
logging.getLogger("agent").setLevel(logging.DEBUG)
```

### 查看 SSE 事件流

浏览器 DevTools → Network → 筛选 `EventStream` → 查看 `/api/ai/chat` 请求的事件流。

### 测试单个 Skill

```python
# 在 Python REPL 中
from database import SessionLocal
from agent import tools as tool_module
from skills.shelf_skill import ShelfSkill

db = SessionLocal()
db_tools = {
    "get_cabinet_structure": lambda cid: tool_module.get_cabinet_structure(db, cid),
    "add_component": lambda **kw: tool_module.add_component(db, **kw),
}
skill = ShelfSkill(db_tools)
result = await skill.execute(cabinet_id=1, params={"count": 2}, context={})
print(result)
```

### 无 LLM 模式

不设置 `LLM_API_KEY` 时，Agent 使用 `SkillRegistry.match_skill()` 做关键词匹配。支持的简单指令：

- 包含"隔板" → ShelfSkill
- 包含"门" → DoorSkill
- 包含"抽屉" → DrawerSkill
- 包含"材质"/"颜色" → MaterialSkill
- 包含"几块"/"多少" → QuerySkill
- 包含"尺寸"/"加高" → ResizeSkill

## SSE 事件类型

| 事件 | data 字段 | 说明 |
|------|-----------|------|
| `thinking` | `{content}` | Agent 正在思考 |
| `skill_selected` | `{skill_id, skill_name, reasoning}` | LLM 选择了 Skill |
| `skill_executing` | `{skill_id, step, progress}` | Skill 执行中 |
| `tool_calls` | `{calls: [{tool, args}]}` | 调用的工具和参数 |
| `skill_completed` | `{skill_id, result, success}` | Skill 执行完成 |
| `message` | `{content}` | 最终文字回复 |
| `done` | `{cabinet_id, operations, skills_used}` | 全部完成 |
| `error` | `{content}` | 错误信息 |

## 文件清单

```
backend/agent/
├── __init__.py
├── agent.py          # CabinetAgent — LLM 调用 + Skill 执行
├── tools.py          # 8 个原子工具函数
├── prompts.py        # System Prompt 模板
└── skill_registry.py # Skill 注册中心

backend/skills/
├── __init__.py       # ALL_SKILLS 列表
├── base.py           # BaseSkill ABC + SkillResult
├── shelf_skill.py    # add_shelf
├── door_skill.py     # add_doors
├── drawer_skill.py   # add_drawers
├── material_skill.py # change_material
├── query_skill.py    # query_structure
├── resize_skill.py   # adjust_cabinet_size
└── layout_skill.py   # reorganize_layout

backend/services/
└── ai_service.py     # AIService — 会话管理 + Agent 调用

backend/routers/
└── ai.py             # POST /api/ai/chat (SSE) + GET /api/ai/skills
```
