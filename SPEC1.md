# 单柜板件级3D编辑器 — 软件规格说明书 (SPEC1)

## 1. 项目概述

### 1.1 项目名称
**CabinetCraft Pro** — 单柜板件级3D在线编辑器

### 1.2 项目目标
构建一个在线3D柜子编辑器，以**单个柜子**为编辑单元，用户可以在板件/组件级别对柜子进行精细化增删改（如添加隔板、替换门板、加抽屉等），同时支持自然语言指令驱动编辑，实现所见即所得的柜子定制设计。

### 1.3 与 SPEC 的核心差异

| 维度 | SPEC (多柜场景编辑) | SPEC1 (单柜板件编辑) |
|------|---------------------|---------------------|
| 编辑粒度 | 整体柜子（位置/尺寸/材质） | 柜子内部板件与组件（侧板/隔板/门板/抽屉） |
| 前端的职责 | 渲染 + 交互 | 渲染 + 交互 + **编辑逻辑**（板件增删改的核心计算） |
| 后端的职责 | CRUD + LLM Agent + 业务逻辑 | 数据持久化 + 历史查询 + **LLM Agent** |
| 核心模型 | 柜子实体 | 板件树/组件树 |

---

## 2. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue 3 + TypeScript | 组件化开发，类型安全 |
| 构建工具 | Vite | 快速HMR，ESBuild打包 |
| 3D渲染 | Three.js | WebGL 3D渲染引擎 |
| 前端状态管理 | Pinia | 柜子板件树状态管理 |
| 后端框架 | FastAPI (Python 3.10+) | 异步高性能API |
| AI Agent | DeepAgents | LLM Agent编排与工具调用 |
| 数据库 | SQLite + SQLAlchemy | 轻量级持久化存储 |
| LLM | OpenAI API / 兼容接口 | 自然语言理解与生成 |

---

## 3. 柜子板件模型

### 3.1 柜子结构定义

一个柜子由以下板件/组件构成层级树：

```
Cabinet（柜子整体）
├── 柜体 (CabinetBody) — 必选，不可删除
│   ├── TopBoard       — 顶板
│   ├── BottomBoard    — 底板
│   ├── LeftBoard      — 左侧板
│   ├── RightBoard     — 右侧板
│   └── BackBoard      — 背板（可选，可删除）
├── 隔板组 (Shelves) — 可选，多块
│   ├── Shelf[0]       — 活动隔板
│   ├── Shelf[1]
│   └── Shelf[n]
├── 门板组 (Doors) — 可选，多扇
│   ├── Door[0]
│   ├── Door[1]
│   └── Door[n]
├── 抽屉组 (Drawers) — 可选，多个
│   ├── Drawer[0]
│   ├── Drawer[1]
│   └── Drawer[n]
├── 五金/配件 (Accessories) — 可选
│   ├── Handle         — 拉手
│   ├── Hinge          — 铰链（装饰）
│   └── Leg            — 柜脚
└── 踢脚线 (Baseboard) — 可选
```

### 3.2 板件类型枚举

| 类型标识 | 中文名 | 必选 | 可否删除 | 说明 |
|----------|--------|------|----------|------|
| `top_board` | 顶板 | 是 | 否 | 柜体顶部封板 |
| `bottom_board` | 底板 | 是 | 否 | 柜体底部封板 |
| `left_board` | 左侧板 | 是 | 否 | 柜体左侧立板 |
| `right_board` | 右侧板 | 是 | 否 | 柜体右侧立板 |
| `back_board` | 背板 | 否 | 是 | 柜体后封板，默认存在 |
| `shelf` | 隔板 | 否 | 是 | 活动隔板，可任意增删 |
| `door` | 门板 | 否 | 是 | 柜门，可多扇 |
| `drawer` | 抽屉 | 否 | 是 | 抽屉单元，含面板+盒体 |
| `handle` | 拉手 | 否 | 是 | 门/抽屉拉手 |
| `leg` | 柜脚 | 否 | 是 | 底部支撑脚 |
| `baseboard` | 踢脚线 | 否 | 是 | 底部装饰条 |

---

## 4. 功能需求

### 4.1 可视化编辑面板 (Panel Editor) — 前端职责

#### 4.1.1 3D视图
- **柜子3D渲染**：实时渲染柜子所有板件，支持旋转/缩放/平移视角
- **板件高亮选中**：点击板件后高亮显示（Outline效果），右侧面板显示该板件属性
- **网格/轴线辅助**：地面网格和坐标轴参考，可开关
- **爆炸视图**：一键展开柜子板件，查看内部结构
- **透视模式**：柜体半透明，查看内部隔板和配件

#### 4.1.2 板件增删改 — 前端核心逻辑

**a) 增（添加板件/组件）**
- 添加隔板：选择位置（距底板高度），自动生成隔板
- 添加门板：选择覆盖区域（全高/半高），自动适配尺寸
- 添加抽屉：选择位置和数量，自动计算抽屉盒尺寸
- 添加背板：一键添加默认尺寸背板
- 添加柜脚：选择数量和位置
- 添加踢脚线：一键添加
- 所有新增板件均需**前端计算**：根据柜体当前尺寸、已有板件位置，自动约束新板件的位置和尺寸

**b) 删（删除板件/组件）**
- 选中板件 → 删除按钮 / Delete键
- 必选板件（顶/底/左/右板）不可删除，UI上灰显删除按钮
- 删除前确认提示
- 删除门板时，关联拉手自动删除

**c) 改（修改板件属性）**
- 板件尺寸：长/宽/厚（受柜体约束限制）
- 板件位置：X/Y/Z偏移（受相邻板件约束）
- 材质切换：每种板件独立选择材质
- 颜色切换：每种板件独立选择颜色
- 门板样式：平板/造型/玻璃/百叶
- 把手样式：隐藏/长条/圆钮（门板和抽屉共用）
- 隔板位置：高度调节（滑块+数值）
- 板件厚度：可调节（默认18mm）

#### 4.1.3 约束系统 — 前端核心

前端必须维护板件之间的约束关系：

```
约束规则（前端自动计算）：
1. 顶板Y = 柜体高度 - 顶板厚度
2. 底板Y = 0
3. 左侧板X = -柜体宽度/2 + 左侧板厚度/2
4. 右侧板X = 柜体宽度/2 - 右侧板厚度/2
5. 背板Z = -柜体深度/2 + 背板厚度/2
6. 隔板Y范围：底板厚度 < Y < 顶板底部
7. 隔板宽度 = 柜体内部宽度（左右侧板间距）
8. 隔板深度 ≤ 柜体内部深度
9. 门板宽度之和 ≤ 柜体宽度
10. 门板高度 ≤ 柜体高度
11. 抽屉总高度之和 ≤ 柜体可用高度
12. 抽屉宽度 = 柜体内部宽度（左右侧板间距）
```

#### 4.1.4 操作历史
- 撤销/重做：Ctrl+Z / Ctrl+Y，记录每次板件操作的快照
- 操作历史面板：显示最近操作列表，可跳转到任意历史状态

### 4.2 自然语言编辑 (AI Editor)

#### 4.2.1 对话式编辑
- **聊天面板**：右侧面板Tab切换至AI对话
- **意图理解**：LLM解析用户自然语言，识别板件级操作意图：
  - 添加板件："在柜子中间加一块隔板"
  - 删除板件："把第二块隔板去掉"
  - 修改板件："把左侧板换成深色胡桃木"
  - 批量操作："把所有隔板改成玻璃材质"
  - 结构调整："上面加两扇对开门，下面加两个抽屉"
  - 尺寸调整："把柜子加高20厘米，隔板也跟着调整"
  - 查询信息："这个柜子有几块隔板？门板是什么材质的？"
- **操作确认**：AI生成操作计划后展示给用户确认
- **实时反馈**：操作完成后刷新3D视图并给出文字总结

#### 4.2.2 Agent工具链
DeepAgents Agent具备以下工具（函数调用）：

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `add_component` | 添加板件/组件 | cabinet_id, component_type, [position], [size], [material], [color], [style] |
| `remove_component` | 删除板件/组件 | cabinet_id, component_id |
| `update_component` | 修改板件属性 | cabinet_id, component_id, 任意修改字段 |
| `get_cabinet_structure` | 获取柜子完整结构树 | cabinet_id |
| `get_component` | 获取单个板件详情 | cabinet_id, component_id |
| `list_components` | 列出某类型所有板件 | cabinet_id, component_type |
| `update_cabinet_size` | 调整柜体整体尺寸 | cabinet_id, width, height, depth |
| `undo` / `redo` | 撤销/重做 | cabinet_id |
| `get_snapshot_description` | 获取柜子结构文字描述（供LLM理解） | cabinet_id |

#### 4.2.3 AI编辑请求流程

```
用户输入 → 前端POST /api/ai/chat
  → 后端获取柜子当前完整结构(get_cabinet_structure作为上下文)
  → DeepAgents Agent推理 → 调用工具函数
  → 后端返回操作指令序列(SSE流式)
  → 前端接收操作指令序列
  → 前端执行板件的增删改逻辑(约束计算、位置调整)
  → Three.js刷新视图
```

**关键设计**：AI只返回"做什么"的操作指令，实际的板件约束计算、位置尺寸推导由前端完成。

---

## 5. 系统架构

### 5.1 整体架构图

```
┌───────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Three.js)              │
│                                                       │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │  3D View    │  │  Panel Editor  │  │ Chat Panel │ │
│  │ (Three.js)  │  │  (板件增删改)   │  │ (AI对话)   │ │
│  └──────┬──────┘  └───────┬────────┘  └─────┬──────┘ │
│         │                 │                  │        │
│         └─────────────────┼──────────────────┘        │
│                           │                           │
│              ┌────────────┴────────────┐              │
│              │  编辑引擎 (核心前端逻辑)  │              │
│              │  - 约束求解器            │              │
│              │  - 板件尺寸计算          │              │
│              │  - 碰撞/重叠检测         │              │
│              │  - 操作快照管理          │              │
│              └────────────┬────────────┘              │
│                           │                           │
│                  Pinia Store (状态管理)                │
│                           │                           │
│                           │  HTTP/SSE                 │
└───────────────────────────┼───────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────┐
│                    后端 (FastAPI)                       │
│  ┌────────────────────────┴──────────────────────┐    │
│  │               API Router                       │    │
│  │  /api/cabinet   柜子数据读写                    │    │
│  │  /api/history   操作历史查询                    │    │
│  │  /api/ai        AI对话(SSE)                    │    │
│  └────────┬──────────────────────────────────────┘    │
│           │                                           │
│  ┌────────┴─────────┐  ┌────────────────────────┐    │
│  │  DataService     │  │   DeepAgents            │    │
│  │  (数据持久化)     │  │   Agent + Tools         │    │
│  └────────┬─────────┘  └────────────┬───────────┘    │
│           │                         │                 │
│  ┌────────┴─────────────────────────┴───────────┐    │
│  │          SQLAlchemy ORM / SQLite              │    │
│  └───────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

### 5.2 前后端职责边界

| 职责 | 前端 | 后端 |
|------|------|------|
| 3D渲染 | ✓ | ✗ |
| 板件增删改UI | ✓ | ✗ |
| 约束求解（位置/尺寸计算） | ✓ | ✗ |
| 板件重叠检测 | ✓ | ✗ |
| 操作撤销/重做 | ✓（运行时） | ✓（持久化历史） |
| 数据持久化（保存/加载） | ✗ | ✓ |
| LLM Agent推理 | ✗ | ✓ |
| 操作历史记录 | ✗ | ✓ |
| 工具函数定义与执行 | ✗ | ✓ |

---

## 6. 数据库设计

### 6.1 表结构

#### cabinets（柜子主表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 柜子唯一ID |
| name | VARCHAR(128) | NOT NULL, DEFAULT '未命名柜子' | 柜子名称 |
| width | FLOAT | NOT NULL, DEFAULT 800 | 柜体总宽度(mm) |
| height | FLOAT | NOT NULL, DEFAULT 2000 | 柜体总高度(mm) |
| depth | FLOAT | NOT NULL, DEFAULT 500 | 柜体总深度(mm) |
| board_thickness | FLOAT | NOT NULL, DEFAULT 18 | 默认板件厚度(mm) |
| global_material | VARCHAR(32) | DEFAULT 'wood_oak' | 全局默认材质 |
| global_color | VARCHAR(16) | DEFAULT '#C49A6C' | 全局默认颜色 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### components（板件/组件表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 板件唯一ID |
| cabinet_id | INTEGER | FK → cabinets.id, NOT NULL | 所属柜子 |
| component_type | VARCHAR(32) | NOT NULL | 类型枚举（见3.2） |
| parent_id | INTEGER | FK → components.id, NULLABLE | 父板件ID（抽屉关联门板等） |
| label | VARCHAR(64) | DEFAULT '' | 板件标签（如 "第2层隔板"） |
| sort_order | INTEGER | DEFAULT 0 | 同类型内排序 |
| width | FLOAT | NOT NULL | 板件宽度(mm) |
| height | FLOAT | NOT NULL | 板件高度(mm) |
| depth | FLOAT | NOT NULL | 板件深度/厚度(mm) |
| position_x | FLOAT | NOT NULL, DEFAULT 0 | 相对柜体原点X偏移(mm) |
| position_y | FLOAT | NOT NULL, DEFAULT 0 | 相对柜体原点Y偏移(mm) |
| position_z | FLOAT | NOT NULL, DEFAULT 0 | 相对柜体原点Z偏移(mm) |
| rotation_x | FLOAT | NOT NULL, DEFAULT 0 | 绕X轴旋转(弧度) |
| rotation_y | FLOAT | NOT NULL, DEFAULT 0 | 绕Y轴旋转(弧度) |
| rotation_z | FLOAT | NOT NULL, DEFAULT 0 | 绕Z轴旋转(弧度) |
| material | VARCHAR(32) | DEFAULT NULL | 材质（NULL=继承全局） |
| color | VARCHAR(16) | DEFAULT NULL | 颜色（NULL=继承全局） |
| door_style | VARCHAR(32) | DEFAULT NULL | 门板样式（仅door类型） |
| handle_style | VARCHAR(32) | DEFAULT NULL | 拉手样式（door/drawer类型） |
| is_enabled | BOOLEAN | DEFAULT TRUE | 是否启用显示 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### operation_history（操作历史表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 历史记录ID |
| cabinet_id | INTEGER | FK → cabinets.id, NOT NULL | 所属柜子 |
| operation_type | VARCHAR(32) | NOT NULL | 操作类型：add/remove/update/resize |
| target_type | VARCHAR(32) | NOT NULL | 目标类型：cabinet/component |
| target_id | INTEGER | NULLABLE | 目标ID |
| snapshot_json | TEXT | NOT NULL | 操作后柜子完整JSON快照 |
| description | VARCHAR(256) | DEFAULT '' | 操作描述（如"添加第2层隔板"） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 操作时间 |

#### ai_chat_history（AI对话历史表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 消息ID |
| cabinet_id | INTEGER | FK → cabinets.id, NOT NULL | 所属柜子 |
| role | VARCHAR(16) | NOT NULL | 角色：user/assistant/system |
| content | TEXT | NOT NULL | 消息内容 |
| tool_calls_json | TEXT | DEFAULT NULL | JSON格式的工具调用记录 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 7. API 接口设计

### 7.1 柜子管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cabinets` | 列出所有柜子 |
| POST | `/api/cabinets` | 创建新柜子（含默认板件初始化） |
| GET | `/api/cabinets/{cabinet_id}` | 获取柜子详情（含所有板件） |
| PUT | `/api/cabinets/{cabinet_id}` | 更新柜子整体属性 |
| DELETE | `/api/cabinets/{cabinet_id}` | 删除柜子及所有板件 |
| PUT | `/api/cabinets/{cabinet_id}/size` | 调整柜体整体尺寸 |

### 7.2 板件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cabinets/{cabinet_id}/components` | 获取柜子所有板件 |
| GET | `/api/cabinets/{cabinet_id}/components/{comp_id}` | 获取单个板件 |
| POST | `/api/cabinets/{cabinet_id}/components` | 添加板件 |
| PUT | `/api/cabinets/{cabinet_id}/components/{comp_id}` | 更新板件 |
| DELETE | `/api/cabinets/{cabinet_id}/components/{comp_id}` | 删除板件 |

### 7.3 操作历史

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cabinets/{cabinet_id}/history` | 获取操作历史列表 |
| GET | `/api/cabinets/{cabinet_id}/history/{history_id}` | 获取某次操作快照 |
| POST | `/api/cabinets/{cabinet_id}/history` | 保存操作快照 |

### 7.4 AI对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | 发送自然语言指令（SSE流式响应） |

**POST /api/ai/chat 请求体：**

```json
{
  "cabinet_id": 1,
  "message": "在柜子中间加两块隔板，上面装两扇玻璃门",
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

event: tool_calls
data: {"calls": [
  {"tool": "add_component", "args": {"component_type": "shelf", "position_y": 660, ...}},
  {"tool": "add_component", "args": {"component_type": "shelf", "position_y": 1320, ...}},
  {"tool": "add_component", "args": {"component_type": "door", "door_style": "glass", ...}}
]}

event: message
data: {"content": "已添加2块隔板和2扇玻璃门，隔板间距约660mm。"}

event: done
data: {"cabinet_id": 1, "component_count": 12}
```

**关键设计**：`tool_calls` 事件中返回的是操作指令序列，前端接收后由编辑引擎执行实际的板件创建、约束计算和3D渲染。

### 7.5 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

## 8. 前端详细设计

### 8.1 页面布局

```
┌──────────────────────────────────────────────────────────┐
│  Header: Logo | 柜子名称[可编辑] | 保存 | 加载 | 撤销/重做 │
├──────────────────────────┬───────────────────────────────┤
│                          │  右侧面板 (360px)              │
│   3D 视图区域             │  ┌─────────────────────────┐  │
│   (Three.js Canvas)      │  │ [属性编辑] [AI对话]      │  │
│                          │  │    Tab 切换              │  │
│                          │  ├─────────────────────────┤  │
│                          │  │                          │  │
│   ┌──────────────┐       │  │  属性编辑模式:            │  │
│   │  柜子3D模型   │       │  │  - 柜子整体属性          │  │
│   │              │       │  │  - 板件列表(树形)        │  │
│   │  顶板          │       │  │  - 选中板件属性编辑     │  │
│   │  ┌──────────┐ │       │  │    · 位置/尺寸         │  │
│   │  │  门板1   │ │       │  │    · 材质/颜色          │  │
│   │  ├──────────┤ │       │  │    · 门板/把手样式      │  │
│   │  │  门板2   │ │       │  │  - 添加板件按钮组       │  │
│   │  └──────────┘ │       │  │                          │  │
│   │  底板          │       │  │  AI对话模式:             │  │
│   └──────────────┘       │  │  - 消息列表              │  │
│                          │  │  - 输入框                 │  │
│  工具栏:                  │  │  - 操作确认卡片          │  │
│  [爆炸] [透视] [重置视角]  │  │                          │  │
│                          │  └─────────────────────────┘  │
├──────────────────────────┴───────────────────────────────┤
│  底部状态栏: 板件数量 | 柜体尺寸 | 材质 | FPS             │
└──────────────────────────────────────────────────────────┘
```

### 8.2 组件树

```
App.vue
├── AppHeader.vue                # 顶部导航栏
│   ├── CabinetNameEditor.vue    # 柜子名称编辑
│   └── ActionButtons.vue        # 保存/加载/撤销/重做
├── MainLayout.vue               # 主体布局
│   ├── ThreeCanvas.vue          # 3D渲染画布（核心）
│   │   ├── CabinetGroup.vue     # 柜子板件群组
│   │   │   └── BoardMesh.vue    # 单块板件Mesh
│   │   ├── GridHelper.vue       # 地面网格
│   │   ├── OrbitControls        # 视角控制
│   │   └── ToolbarOverlay.vue   # 浮动工具栏(爆炸/透视)
│   ├── RightPanel.vue           # 右侧面板
│   │   ├── PropertyTab.vue      # 属性编辑Tab
│   │   │   ├── CabinetInfo.vue      # 柜子整体信息
│   │   │   ├── ComponentTree.vue    # 板件树形列表
│   │   │   ├── ComponentEditor.vue  # 选中板件属性编辑器
│   │   │   │   ├── PositionEditor.vue
│   │   │   │   ├── SizeEditor.vue
│   │   │   │   └── StyleEditor.vue
│   │   │   └── AddComponentPanel.vue # 添加板件按钮组
│   │   └── AITab.vue            # AI对话Tab
│   │       ├── ChatMessages.vue
│   │       ├── OperationConfirm.vue  # 操作确认卡片
│   │       └── ChatInput.vue
│   └── StatusBar.vue            # 底部状态栏
└── ConfirmDialog.vue            # 通用确认对话框
```

### 8.3 编辑引擎 (核心前端模块)

```typescript
// engine/ConstraintSolver.ts — 约束求解器
class ConstraintSolver {
  /** 根据柜体尺寸计算必选板件位置 */
  static computeBodyBoards(cabinet: CabinetSize): BoardPlacement[]

  /** 计算新隔板的默认位置（在可用空间居中） */
  static computeShelfPlacement(cabinet: CabinetData, targetY?: number): BoardPlacement

  /** 计算门板的默认尺寸（适配柜体正面） */
  static computeDoorPlacement(cabinet: CabinetData, count: number, style: DoorStyle): BoardPlacement[]

  /** 计算抽屉的默认尺寸和位置 */
  static computeDrawerPlacement(cabinet: CabinetData, count: number, startY: number): BoardPlacement[]

  /** 验证板件是否与其他板件重叠 */
  static checkOverlap(component: Component, allComponents: Component[]): boolean

  /** 获取柜体内部可用空间 */
  static getInternalSpace(cabinet: CabinetData): BoundingBox
}

// engine/BoardFactory.ts — 板件工厂
class BoardFactory {
  /** 根据类型创建默认板件数据 */
  static create(type: ComponentType, cabinet: CabinetData, options?: Partial<Component>): Component

  /** 根据板件数据生成Three.js Mesh */
  static createMesh(component: Component): THREE.Mesh

  /** 更新已有Mesh的属性 */
  static updateMesh(mesh: THREE.Mesh, component: Component): void
}

// engine/SnapshotManager.ts — 操作快照管理
class SnapshotManager {
  private undoStack: CabinetSnapshot[] = []
  private redoStack: CabinetSnapshot[] = []

  takeSnapshot(cabinet: CabinetData): void
  undo(): CabinetSnapshot | null
  redo(): CabinetSnapshot | null
  canUndo(): boolean
  canRedo(): boolean
}
```

### 8.4 Pinia Store

```typescript
// stores/cabinet.ts
interface CabinetStore {
  cabinet: Cabinet | null                    // 柜子元数据
  components: Component[]                    // 所有板件列表
  selectedComponentId: number | null         // 当前选中板件
  snapshotManager: SnapshotManager           // 快照管理器
  viewMode: 'normal' | 'exploded' | 'xray'  // 视图模式
  isDirty: boolean                           // 是否有未保存修改

  // Actions
  loadCabinet(id: number): Promise<void>
  saveCabinet(): Promise<void>
  addComponent(type: ComponentType, options?: Partial<Component>): void
  removeComponent(id: number): void
  updateComponent(id: number, changes: Partial<Component>): void
  selectComponent(id: number | null): void
  applyAIOperations(operations: AIOperation[]): void
}

// stores/chat.ts
interface ChatStore {
  messages: ChatMessage[]
  isStreaming: boolean
  pendingOperations: AIOperation[] | null    // 待确认的操作

  sendMessage(cabinetId: number, text: string): Promise<void>
  confirmOperations(): void
  rejectOperations(): void
}
```

### 8.5 Three.js 渲染方案

- **板件建模**：每块板件使用 `BoxGeometry(w, h, d)` 创建，厚度方向为最小维度
- **材质系统**：
  - `MeshStandardMaterial` 用于不透明板件（木板、烤漆板）
  - `MeshPhysicalMaterial` 用于玻璃等透明材质（door_style=glass）
  - 预设纹理贴图用于木纹材质
- **选中高亮**：`OutlineEffect` 或 `EdgesGeometry` + `LineBasicMaterial` 绘制发光边框
- **光照**：环境光(0.4) + 方向光(0.8) + 半球光(0.3, 0.1)，模拟室内光照
- **阴影**：`PCFSoftShadowMap`
- **射线检测**：`Raycaster` 实现板件点击选中
- **柜子坐标系**：柜子几何中心为原点(0,0,0)，X=宽度方向，Y=高度方向，Z=深度方向
- **爆炸视图**：每块板件沿法线方向偏移一定距离
- **透视模式**：非选中板件设置 `material.opacity = 0.3`，`material.transparent = true`

---

## 9. 后端详细设计

### 9.1 项目结构

```
backend/
├── main.py                     # FastAPI入口 + CORS配置
├── config.py                   # 配置（数据库URL、LLM配置等）
├── database.py                 # SQLAlchemy引擎 + Session管理
├── models/
│   ├── __init__.py
│   ├── cabinet.py              # Cabinet ORM模型
│   ├── component.py            # Component ORM模型
│   ├── operation_history.py    # OperationHistory ORM模型
│   └── ai_chat.py              # AIChatHistory ORM模型
├── schemas/
│   ├── __init__.py
│   ├── cabinet.py              # Pydantic请求/响应模型
│   ├── component.py
│   ├── history.py
│   └── ai.py
├── routers/
│   ├── __init__.py
│   ├── cabinets.py             # 柜子CRUD路由
│   ├── components.py           # 板件CRUD路由
│   ├── history.py              # 操作历史路由
│   └── ai.py                   # AI对话路由（SSE）
├── services/
│   ├── __init__.py
│   ├── cabinet_service.py      # 柜子数据服务
│   ├── component_service.py    # 板件数据服务
│   ├── history_service.py      # 操作历史服务
│   └── ai_service.py           # AI对话编排服务
├── agent/
│   ├── __init__.py
│   ├── agent.py                # DeepAgents Agent定义
│   ├── tools.py                # Agent工具函数定义
│   └── prompts.py              # System Prompt模板
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures (测试数据库)
    ├── test_cabinets.py
    ├── test_components.py
    ├── test_history.py
    └── test_ai.py
```

### 9.2 CabinetService

```python
class CabinetService:
    """柜子数据服务 — 仅负责数据持久化，不含编辑逻辑"""

    def create_default(self, name: str = "未命名柜子") -> Cabinet:
        """创建新柜子并初始化默认必选板件（顶/底/左/右/背板）"""

    def get_with_components(self, cabinet_id: int) -> Cabinet:
        """获取柜子及其所有板件"""

    def update(self, cabinet_id: int, data: CabinetUpdate) -> Cabinet:
        """更新柜子元数据"""

    def update_size(self, cabinet_id: int, width: float, height: float, depth: float) -> Cabinet:
        """更新柜体尺寸（板件位置由前端重新计算后提交）"""

    def delete(self, cabinet_id: int) -> None:
        """级联删除柜子及所有关联数据"""

    def list_all(self) -> list[Cabinet]:
        """列出所有柜子摘要"""
```

### 9.3 ComponentService

```python
class ComponentService:
    """板件数据服务 — 纯CRUD，不含约束计算"""

    def list_by_cabinet(self, cabinet_id: int) -> list[Component]:
        """获取柜子所有板件"""

    def get(self, component_id: int) -> Component:
        """获取单个板件"""

    def create(self, cabinet_id: int, data: ComponentCreate) -> Component:
        """创建板件（位置/尺寸由前端计算好后提交）"""

    def update(self, component_id: int, data: ComponentUpdate) -> Component:
        """更新板件属性"""

    def delete(self, component_id: int) -> None:
        """删除板件（前端保证不是必选板件）"""

    def batch_replace(self, cabinet_id: int, components: list[ComponentCreate]) -> list[Component]:
        """批量替换所有板件（用于AI操作后前端整体提交）"""
```

### 9.4 DeepAgents Agent 设计

```python
# agent/agent.py
from deepagents import Agent

class CabinetAgent:
    def __init__(self, llm_client, tools: list):
        self.agent = Agent(
            model=llm_client,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )

    async def chat_stream(
        self,
        cabinet_id: int,
        message: str,
        history: list[dict]
    ) -> AsyncGenerator[str, None]:
        """流式对话，生成SSE事件"""
```

```python
# agent/prompts.py
SYSTEM_PROMPT = """
你是一个柜子板件级3D编辑助手。用户会通过自然语言描述想对柜子内部结构进行的修改。

你需要理解用户的意图，并调用合适的工具来生成操作指令。

## 柜子结构说明
- 一个柜子由多种板件组成：顶板、底板、左侧板、右侧板、背板（必选）、隔板、门板、抽屉等
- 坐标原点在柜体几何中心，(0,0,0)
- X轴=宽度方向，Y轴=高度方向，Z轴=深度方向
- 尺寸单位：毫米(mm)

## 板件类型
- top_board: 顶板（必选，不可删除）
- bottom_board: 底板（必选，不可删除）
- left_board: 左侧板（必选，不可删除）
- right_board: 右侧板（必选，不可删除）
- back_board: 背板
- shelf: 隔板
- door: 门板
- drawer: 抽屉
- handle: 拉手
- leg: 柜脚
- baseboard: 踢脚线

## 操作规则
1. 不要删除必选板件（顶板、底板、左侧板、右侧板）
2. 添加板件前，先调用 get_cabinet_structure 了解当前柜子结构
3. 添加板件时，给出合理的位置和尺寸参数。如果用户没有指定具体数值，使用合理的默认值
4. 隔板和抽屉的默认位置应避免与已有板件重叠
5. 门板的默认尺寸应适配柜体正面
6. 用户说"中间"时，Y坐标取柜体高度的一半
7. 用户说"上面/顶部"时，Y坐标靠近顶板下方
8. 用户说"下面/底部"时，Y坐标靠近底板上方
9. 板件厚度默认为18mm
10. 背板厚度默认为5mm

## 回复要求
- 操作完成后，用简洁的中文总结做了什么
- 如果用户指令不明确，先询问澄清而不是猜测
"""
```

### 9.5 Agent 工具函数

```python
# agent/tools.py
@tool
async def get_cabinet_structure(cabinet_id: int) -> str:
    """获取柜子完整板件结构，返回JSON格式的板件列表，供AI理解当前状态"""
    ...

@tool
async def add_component(
    cabinet_id: int,
    component_type: str,
    position_y: float = None,
    position_x: float = None,
    position_z: float = None,
    width: float = None,
    height: float = None,
    depth: float = None,
    material: str = None,
    color: str = None,
    door_style: str = None,
    handle_style: str = None,
    count: int = 1
) -> str:
    """生成添加板件的操作指令"""
    ...

@tool
async def remove_component(cabinet_id: int, component_id: int) -> str:
    """生成删除板件的操作指令"""
    ...

@tool
async def update_component(
    cabinet_id: int,
    component_id: int,
    material: str = None,
    color: str = None,
    door_style: str = None,
    handle_style: str = None,
    position_y: float = None,
    width: float = None,
    height: float = None,
    depth: float = None
) -> str:
    """生成修改板件属性的操作指令"""
    ...

@tool
async def update_cabinet_size(
    cabinet_id: int,
    width: float = None,
    height: float = None,
    depth: float = None
) -> str:
    """生成调整柜体尺寸的操作指令"""
    ...

@tool
async def list_components(cabinet_id: int, component_type: str = None) -> str:
    """列出柜子中指定类型的所有板件"""
    ...
```

---

## 10. 交互流程

### 10.1 可视化编辑流程

```
用户打开/创建柜子
  → GET /api/cabinets/{id} 获取柜子 + 所有板件
  → BoardFactory 为每块板件创建 Three.js Mesh
  → 渲染完整柜子3D模型

用户点击"添加隔板"
  → ConstraintSolver.computeShelfPlacement() 计算默认位置
  → BoardFactory.create('shelf', ...) 创建板件数据
  → BoardFactory.createMesh() 创建Mesh添加到场景
  → SnapshotManager.takeSnapshot() 记录快照
  → POST /api/cabinets/{id}/components 持久化

用户选中隔板
  → Raycaster 检测点击
  → OutlineEffect 高亮选中
  → 右侧面板显示属性编辑器

用户拖动隔板高度滑块
  → ConstraintSolver 验证新位置不越界
  → 更新 component.position_y
  → BoardFactory.updateMesh() 更新Mesh位置
  → 实时 3D 预览（防抖200ms后才持久化）

用户修改材质
  → 更新 component.material
  → BoardFactory.updateMesh() 替换材质
  → PUT /api/cabinets/{id}/components/{cid} 持久化

用户删除隔板
  → ConfirmDialog 确认
  → SnapshotManager.takeSnapshot()
  → 从场景移除Mesh
  → DELETE /api/cabinets/{id}/components/{cid}

用户撤销 (Ctrl+Z)
  → SnapshotManager.undo()
  → 根据快照重建板件列表和3D场景
```

### 10.2 AI对话编辑流程

```
用户输入: "在柜子中间加一块玻璃隔板，上面装两扇白色烤漆门"

前端:
  → POST /api/ai/chat { cabinet_id, message, history } (SSE)

后端:
  → get_cabinet_structure(cabinet_id) 获取当前板件结构注入上下文
  → Agent推理:
     1. 柜子高2000mm，中间约1000mm处
     2. 内部宽度 = 柜宽 - 左右板厚度 = 800-18-18 = 764mm
     3. 隔板: shelf, Y=1000, 玻璃材质
     4. 门板: 2扇, 覆盖上半部分(Y=1000到2000), 白色烤漆
  → SSE: thinking → "正在分析柜子结构并规划操作..."
  → SSE: tool_calls → [
      {tool: "add_component", args: {type:"shelf", position_y:1000, material:"glass"}},
      {tool: "add_component", args: {type:"door", count:2, position_y:1000, height:982, material:"paint_white"}}
    ]
  → SSE: message → "已添加玻璃隔板(高1000mm处)和2扇白色烤漆门"
  → SSE: done

前端:
  → 接收 tool_calls → 展示操作确认卡片
  → 用户点击"确认"
  → 前端编辑引擎逐条执行:
      1. ConstraintSolver 计算隔板精确位置和尺寸
      2. BoardFactory 创建隔板Mesh
      3. ConstraintSolver 计算门板尺寸(需减去隔板厚度)
      4. BoardFactory 创建2扇门板Mesh
  → SnapshotManager 记录快照
  → POST /api/cabinets/{id}/components 批量持久化
  → 3D视图更新完成
```

### 10.3 保存/加载流程

```
保存:
  用户点击保存
  → 前端收集当前 cabinet + components 状态
  → PUT /api/cabinets/{id} 更新柜子元数据
  → PUT /api/cabinets/{id}/components/batch 批量更新板件
  → POST /api/cabinets/{id}/history 保存操作快照
  → 提示保存成功

加载:
  用户从列表选择柜子
  → GET /api/cabinets/{id} 获取柜子数据 + 板件列表
  → 前端重建 Three.js 场景
  → SnapshotManager 清空undo/redo栈
```

---

## 11. 错误处理

### 11.1 后端错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| CABINET_NOT_FOUND | 404 | 柜子不存在 |
| COMPONENT_NOT_FOUND | 404 | 板件不存在 |
| COMPONENT_REQUIRED | 403 | 该板件为必选板件，不可删除 |
| INVALID_PARAMS | 400 | 参数校验失败 |
| INVALID_COMPONENT_TYPE | 400 | 无效的板件类型 |
| SIZE_OUT_OF_RANGE | 400 | 尺寸超出合理范围 |
| AI_SERVICE_ERROR | 500 | AI服务调用失败 |
| AI_TIMEOUT | 504 | AI服务响应超时 |

### 11.2 前端错误处理

- API调用失败：Toast通知，保留本地修改状态
- AI流式响应中断：显示已接收的操作指令，用户可选择执行或放弃
- 3D渲染异常：显示降级提示"3D渲染异常，请刷新页面"
- 约束冲突：面板上红框提示冲突参数，阻止提交
- 网络断开：自动保存到 localStorage，恢复连接后提示同步

---

## 12. 测试策略

### 12.1 前端单元测试（Vitest）

| 测试模块 | 测试内容 |
|----------|----------|
| `ConstraintSolver.test.ts` | 必选板件位置计算、隔板默认位置、门板尺寸计算、空间重叠检测 |
| `BoardFactory.test.ts` | 板件数据创建正确性、Mesh生成参数正确性 |
| `SnapshotManager.test.ts` | 快照创建、撤销、重做、栈边界 |
| `CabinetStore.test.ts` | 增删改状态变更、选中切换、AI操作应用 |
| 组件测试 | 属性面板渲染、板件列表树显示、操作按钮状态 |

### 12.2 后端单元测试（pytest）

| 测试模块 | 测试内容 |
|----------|----------|
| `test_cabinets.py` | 柜子CRUD接口、默认板件初始化、级联删除 |
| `test_components.py` | 板件CRUD接口、必选板件删除校验、批量替换 |
| `test_history.py` | 操作历史记录、快照保存/恢复 |
| `test_ai.py` | Mock LLM → 验证SSE事件格式、工具调用参数正确性 |
| `test_agent_tools.py` | 各工具函数的输入输出正确性 |

### 12.3 集成测试

- 前后端联调：创建柜子 → 添加板件 → 保存 → 加载验证一致性
- AI完整流程：发送指令 → 接收tool_calls → 前端执行 → 持久化 → 加载验证

---

## 13. 开发环境与运行

### 13.1 前端

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
npm run build
npm run test
npm run test:coverage  # 覆盖率报告
```

### 13.2 后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload  # http://localhost:8000
pytest -v --cov=.       # 测试 + 覆盖率
```

### 13.3 依赖清单

**前端 (package.json)**

```json
{
  "dependencies": {
    "vue": "^3.4",
    "pinia": "^2.1",
    "three": "^0.168",
    "axios": "^1.7"
  },
  "devDependencies": {
    "vite": "^5.4",
    "typescript": "^5.5",
    "@vitejs/plugin-vue": "^5.1",
    "vitest": "^2.0",
    "@vue/test-utils": "^2.4"
  }
}
```

**后端 (requirements.txt)**

```
fastapi==0.112.*
uvicorn[standard]==0.30.*
sqlalchemy==2.0.*
pydantic==2.*
deepagents==0.*
httpx==0.27.*
pytest==8.*
pytest-cov==5.*
pytest-asyncio==0.24.*
```

### 13.4 环境变量

```
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，兼容接口
DATABASE_URL=sqlite:///./cabinet_craft.db
```

---

## 14. 版本规划

### V1.0 — MVP
- 单柜基础板件结构（顶/底/左/右/背板 + 默认隔板/门板）
- 可视化编辑面板（增删改板件）
- 前端约束求解器（基础规则）
- AI对话编辑（添加/删除/修改板件）
- 撤销/重做
- 保存/加载

### V1.1 — 功能增强
- 抽屉组件完整支持（含滑轨动画）
- 板件纹理贴图上传
- 爆炸视图动画
- 孔位/连接件显示
- 导出设计参数表（Excel/PDF）
- 柜子模板市场

### V1.2 — 进阶
- 多柜组合编辑
- 真实五金件模型
- AR预览
- 报价单生成
- 对接生产系统（导出CNC数据）

---

## 附录 A：默认柜体初始化板件参数

创建新柜子（默认 宽800 × 高2000 × 深500，板厚18mm）时，前端自动生成以下板件：

| 板件类型 | 宽度(mm) | 高度(mm) | 深度(mm) | Y偏移 | 材质 | 备注 |
|----------|----------|----------|----------|-------|------|------|
| top_board | 800 | 18 | 500 | +991 | wood_oak | 顶板 |
| bottom_board | 800 | 18 | 500 | -991 | wood_oak | 底板 |
| left_board | 18 | 1964 | 500 | 0 | wood_oak | 左侧板(高=2000-18-18) |
| right_board | 18 | 1964 | 500 | 0 | wood_oak | 右侧板 |
| back_board | 764 | 1964 | 5 | 0 | wood_oak | 背板(宽=800-18-18, 厚5mm) |
| door[0] | 382 | 1964 | 18 | 0 | wood_oak | 左门板 |
| door[1] | 382 | 1964 | 18 | 0 | wood_oak | 右门板 |
| handle[0] | - | - | - | - | metal_steel | 左门拉手(关联door[0]) |
| handle[1] | - | - | - | - | metal_steel | 右门拉手(关联door[1]) |

---

## 附录 B：板件材质预设

| 材质标识 | 显示名称 | 颜色 | 说明 |
|----------|----------|------|------|
| wood_oak | 橡木 | #C49A6C | 浅棕木纹 |
| wood_walnut | 胡桃木 | #6B4226 | 深棕木纹 |
| wood_maple | 枫木 | #E8C596 | 浅黄木纹 |
| wood_cherry | 樱桃木 | #A0522D | 红棕木纹 |
| paint_white | 白色烤漆 | #F5F5F5 | 高光白 |
| paint_black | 黑色烤漆 | #2C2C2C | 高光黑 |
| paint_grey | 灰色烤漆 | #A0A0A0 | 中性灰 |
| paint_blue | 蓝色烤漆 | #5B8BD4 | 雾蓝 |
| metal_steel | 不锈钢 | #C0C0C0 | 拉丝金属 |
| metal_gold | 金色 | #D4AF37 | 香槟金 |
| glass_clear | 透明玻璃 | rgba(200,220,255,0.4) | 半透明 |
| glass_frosted | 磨砂玻璃 | rgba(220,230,245,0.6) | 半透明雾面 |

---

## 附录 C：板件约束规则（完整）

```
柜体坐标系：原点 = 柜体几何中心
  X ∈ [-width/2, +width/2]   宽度方向
  Y ∈ [-height/2, +height/2]  高度方向
  Z ∈ [-depth/2, +depth/2]    深度方向

顶板:
  position_y = +(height/2 - top_thickness/2)
  size: width × top_thickness × depth

底板:
  position_y = -(height/2 - bottom_thickness/2)
  size: width × bottom_thickness × depth

左侧板:
  position_x = -(width/2 - left_thickness/2)
  size: left_thickness × (height - top_thickness - bottom_thickness) × depth

右侧板:
  position_x = +(width/2 - right_thickness/2)
  size: right_thickness × (height - top_thickness - bottom_thickness) × depth

背板:
  position_z = -(depth/2 - back_thickness/2)
  size: (width - left_thickness - right_thickness) × (height - top_thickness - bottom_thickness) × back_thickness

隔板(shelf):
  宽度 = width - left_thickness - right_thickness - shelf_clearance
  深度 = depth - back_thickness - shelf_clearance
  Y范围: -(height/2 - bottom_thickness) + shelf_thickness/2  ~  +(height/2 - top_thickness) - shelf_thickness/2
  默认厚度 = board_thickness

门板(door):
  覆盖区域Y范围: 由用户指定或默认全高
  单扇宽度 = (width - gap_total) / door_count
  高度 = 覆盖区域高度 - top_gap - bottom_gap
  默认厚度 = 18mm
  位置Z = +(depth/2 + door_thickness/2)  (柜体前方)

抽屉(drawer):
  宽度 = width - left_thickness - right_thickness - drawer_clearance
  单个抽屉高度 = (可用高度 - gap_total) / drawer_count
  默认厚度: 面板18mm, 盒体12mm
```
