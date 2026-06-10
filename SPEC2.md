# 单柜板件级3D编辑器（Agent + Skills）— 软件规格说明书 (SPEC2)

## 1. 项目概述

### 1.1 项目名称
**CabinetCraft Pro** — 单柜板件级3D在线编辑器（Skills增强版）

### 1.2 项目目标
构建一个在线3D柜子编辑器，以**单个柜子**为编辑单元，在板件/组件级别进行精细化增删改。后端引入 **LLM Agent + Skills** 架构，将柜子设计领域的操作能力封装为可组合、可复用的技能模块（Skills），Agent 根据用户意图动态选择并编排 Skills，实现更智能、更可靠的自然语言编辑体验。

### 1.3 与前版本的差异

| 维度 | SPEC1 (Agent版) | SPEC2 (Agent + Skills版) |
|------|-----------------|--------------------------|
| Agent 能力组织 | 扁平化工具函数列表 | **分层技能体系**：Skills → Tools |
| 领域知识注入 | 仅靠 System Prompt | **Skill 内嵌领域规则**（约束、默认值、材质库） |
| 复杂操作 | 多次工具调用串行 | **Skill 编排**：一个 Skill 可包含多步工具链 |
| 可扩展性 | 新增工具需改 Agent | **插件化 Skill**：新增设计能力 = 新增 Skill 文件 |
| 错误恢复 | Agent 自行重试 | **Skill 内置校验与回滚** |
| 测试粒度 | Agent 集成测试 | Skill 单元测试 + Agent 编排测试 |

---

## 2. 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | Vue 3 + TypeScript | 组件化开发，类型安全 |
| 构建工具 | Vite | 快速HMR，ESBuild打包 |
| 3D渲染 | Three.js | WebGL 3D渲染引擎 |
| 前端状态管理 | Pinia | 柜子板件树状态管理 |
| 后端框架 | FastAPI (Python 3.10+) | 异步高性能API |
| AI Agent | DeepAgents | LLM Agent 编排与工具调用 |
| Agent Skills | 自定义 Skill 模块 | 领域技能封装（见第10节） |
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

### 4.2 自然语言编辑 (AI Editor + Skills)

#### 4.2.1 对话式编辑
- **聊天面板**：右侧面板Tab切换至AI对话
- **意图理解**：LLM解析用户自然语言，Agent 自动匹配并调用对应 Skill
- 意图示例：
  - 添加板件："在柜子中间加一块隔板"
  - 删除板件："把第二块隔板去掉"
  - 修改板件："把左侧板换成深色胡桃木"
  - 批量操作："把所有隔板改成玻璃材质"
  - 结构调整："上面加两扇对开门，下面加两个抽屉"
  - 尺寸调整："把柜子加高20厘米，隔板也跟着调整"
  - 查询信息："这个柜子有几块隔板？门板是什么材质的？"
- **操作确认**：AI生成操作计划后展示给用户确认
- **实时反馈**：操作完成后刷新3D视图并给出文字总结

#### 4.2.2 Skills 体系（核心新增）

Skills 是对柜子设计领域操作的语义化封装，每个 Skill 包含：
- **Skill 描述**：LLM 用于意图匹配的语义说明
- **领域规则**：内置的约束条件、默认值、计算公式
- **工具链**：该 Skill 内部调用的原子工具序列
- **校验逻辑**：操作前后的合法性检查
- **回滚策略**：校验失败时的恢复逻辑

**Skill 列表：**

| Skill ID | Skill 名称 | 功能描述 | 参数 |
|----------|-----------|----------|------|
| `add_shelf` | 添加隔板 | 在指定高度添加一块或多块隔板 | cabinet_id, position_ratios: float[]（0~1相对高度），material?, color? |
| `add_doors` | 添加门板 | 添加指定数量、样式、覆盖范围的门板 | cabinet_id, count: int, style: str, cover_range: "full"\|"upper"\|"lower", material?, color? |
| `add_drawers` | 添加抽屉 | 在指定区域添加抽屉组 | cabinet_id, count: int, start_ratio: float, end_ratio: float, style?, material?, color? |
| `add_backboard` | 添加背板 | 为柜体添加背板 | cabinet_id, material?, color?, thickness? |
| `add_legs` | 添加柜脚 | 添加底部支撑脚 | cabinet_id, count: int = 4, height: float = 100 |
| `add_baseboard` | 添加踢脚线 | 添加底部装饰条 | cabinet_id, height: float = 80, material?, color? |
| `remove_components` | 删除板件 | 按类型或ID删除板件（自动过滤必选板件） | cabinet_id, component_ids?: int[], component_types?: str[] |
| `change_material` | 批量换材质 | 将指定类型板件的材质统一替换 | cabinet_id, component_types: str[], material: str, color? |
| `adjust_cabinet_size` | 调整柜体尺寸 | 调整柜体整体尺寸并触发板件连锁更新 | cabinet_id, width?, height?, depth? |
| `reorganize_layout` | 重新布局 | 复杂结构调整（如"上面两门下面三抽屉"） | cabinet_id, layout_spec: dict |
| `replace_door_style` | 替换门板样式 | 批量更换门板样式 | cabinet_id, style: str, door_ids?: int[] |
| `query_structure` | 查询柜子结构 | 获取柜子结构描述和板件统计 | cabinet_id |
| `balance_shelves` | 均匀分布隔板 | 在柜体内部均匀分布N块隔板 | cabinet_id, count: int, exclude_zones?: list |

**Skill 编排示例：**

用户说"上面加两扇玻璃对开门，下面加三个抽屉"：

```
Agent 意图解析 →
  Skill: reorganize_layout
    ├── 子调用1: add_doors(count=2, style="glass", cover_range="upper")
    │     ├── Tool: get_cabinet_structure → 获取柜体现状
    │     ├── Tool: remove_components(component_types=["door"]) → 清除旧门板
    │     ├── [计算] 上门区域 = 柜体上半部分
    │     ├── Tool: add_component × 2 → 创建两扇门板
    │     └── Tool: add_component → 添加配套拉手
    ├── 子调用2: add_drawers(count=3, cover_range="lower")
    │     ├── [计算] 下抽屉区域 = 柜体下半部分
    │     ├── Tool: add_component × 3 → 创建三个抽屉
    │     └── Tool: add_component × 3 → 添加配套拉手
    └── 校验: 门板+抽屉高度之和 ≤ 柜体高度 ✓
```

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
│  │  DataService     │  │   Agent 层               │    │
│  │  (数据持久化)     │  │  ┌───────────────────┐  │    │
│  └────────┬─────────┘  │  │  DeepAgents Agent  │  │    │
│           │            │  │  (意图路由+编排)    │  │    │
│           │            │  └────────┬──────────┘  │    │
│           │            │           │              │    │
│           │            │  ┌────────┴──────────┐  │    │
│           │            │  │   Skills 层         │  │    │
│           │            │  │  ┌──────┬──────┐  │  │    │
│           │            │  │  │Shelf │Door  │  │  │    │
│           │            │  │  │Skill │Skill  │  │  │    │
│           │            │  │  ├──────┼──────┤  │  │    │
│           │            │  │  │Drawer│Layout│  │  │    │
│           │            │  │  │Skill │Skill  │  │  │    │
│           │            │  │  ├──────┴──────┤  │  │    │
│           │            │  │  │  ...更多     │  │  │    │
│           │            │  │  └────────────┘  │  │    │
│           │            │  └────────┬──────────┘  │    │
│           │            │           │              │    │
│           │            │  ┌────────┴──────────┐  │    │
│           │            │  │   Tools 层          │  │    │
│           │            │  │  (原子操作用具)     │  │    │
│           │            │  └────────────────────┘  │    │
│           │            └────────────────────────────┘    │
│           │                         │                   │
│  ┌────────┴─────────────────────────┴───────────┐      │
│  │          SQLAlchemy ORM / SQLite              │      │
│  └───────────────────────────────────────────────┘      │
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
| LLM Agent 意图路由 | ✗ | ✓ |
| Skill 编排与执行 | ✗ | ✓ |
| Skill 领域规则校验 | ✗ | ✓ |
| 操作历史记录 | ✗ | ✓ |

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
| skill_used | VARCHAR(64) | DEFAULT NULL | 使用的 Skill ID |
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
| GET | `/api/ai/skills` | 获取可用 Skills 列表及描述 |

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

**SSE事件流格式（增强版，含 Skill 信息）：**

```
event: thinking
data: {"content": "正在分析你的需求..."}

event: skill_selected
data: {"skill_id": "add_shelf", "skill_name": "添加隔板", "reasoning": "用户要求添加隔板"}

event: skill_executing
data: {"skill_id": "add_shelf", "step": "计算隔板位置", "progress": "1/3"}

event: tool_calls
data: {"calls": [
  {"tool": "add_component", "args": {"component_type": "shelf", "position_y": 660, ...}},
  {"tool": "add_component", "args": {"component_type": "shelf", "position_y": 1320, ...}}
]}

event: skill_completed
data: {"skill_id": "add_shelf", "result": "成功添加2块隔板"}

event: skill_selected
data: {"skill_id": "add_doors", "skill_name": "添加门板", "reasoning": "用户要求添加玻璃门"}

event: tool_calls
data: {"calls": [
  {"tool": "add_component", "args": {"component_type": "door", "door_style": "glass", ...}}
]}

event: skill_completed
data: {"skill_id": "add_doors", "result": "成功添加2扇玻璃门"}

event: message
data: {"content": "已完成：添加2块隔板（间距均匀分布），2扇玻璃对开门。"}

event: done
data: {"cabinet_id": 1, "component_count": 14, "skills_used": ["add_shelf", "add_doors"]}
```

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
│                          │  │  - Skill 执行进度卡片     │  │
│  工具栏:                  │  │  - 操作确认卡片          │  │
│  [爆炸] [透视] [重置视角]  │  │  - 输入框                 │  │
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
│   │       ├── SkillProgressCard.vue  # Skill执行进度（新增）
│   │       ├── OperationConfirm.vue   # 操作确认卡片
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

  /** 计算新隔板的默认位置（在可用空间居中或均匀分布） */
  static computeShelfPlacement(cabinet: CabinetData, targetY?: number, count?: number): BoardPlacement[]

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
  currentSkill: { skillId: string; skillName: string; progress: string } | null
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
│   ├── tools.py                # Agent原子工具函数定义
│   ├── prompts.py              # System Prompt模板
│   └── skill_registry.py       # Skill注册中心（新增）
├── skills/                     # Skills模块（新增）
│   ├── __init__.py
│   ├── base.py                 # Skill基类 + SkillResult
│   ├── shelf_skill.py          # 隔板相关Skills
│   ├── door_skill.py           # 门板相关Skills
│   ├── drawer_skill.py         # 抽屉相关Skills
│   ├── layout_skill.py         # 布局调整Skills
│   ├── material_skill.py       # 材质/样式Skills
│   ├── query_skill.py          # 查询Skills
│   └── resize_skill.py         # 尺寸调整Skills
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures (测试数据库)
    ├── test_cabinets.py
    ├── test_components.py
    ├── test_history.py
    ├── test_ai.py
    └── test_skills/            # Skills单元测试（新增）
        ├── __init__.py
        ├── test_shelf_skill.py
        ├── test_door_skill.py
        ├── test_drawer_skill.py
        └── test_layout_skill.py
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
    def __init__(self, llm_client, skill_registry: SkillRegistry):
        self.skill_registry = skill_registry
        self.agent = Agent(
            model=llm_client,
            tools=skill_registry.get_all_skill_tools(),  # 注册 Skills 暴露的工具入口
            system_prompt=SYSTEM_PROMPT
        )

    async def chat_stream(
        self,
        cabinet_id: int,
        message: str,
        history: list[dict]
    ) -> AsyncGenerator[str, None]:
        """流式对话，生成SSE事件（含 skill_selected / skill_executing / skill_completed 事件）"""
```

### 9.5 Agent 原子工具层 (Tools)

工具层提供原子操作函数，被 Skills 调用：

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

---

## 10. Skills 体系详细设计（核心新增）

### 10.1 Skill 基类设计

```python
# skills/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class SkillResult:
    """Skill 执行结果"""
    success: bool
    message: str                          # 用户可读的执行描述
    operations: list[dict]                # 返回给前端的操作指令序列
    error: Optional[str] = None

class BaseSkill(ABC):
    """所有 Skill 的抽象基类"""

    skill_id: str                         # 唯一标识
    skill_name: str                       # 中文名称
    description: str                      # 功能描述（给LLM做意图匹配）
    examples: list[str]                   # 触发该 Skill 的自然语言示例

    def __init__(self, tools: dict):
        """
        tools: 原子工具函数字典，如 {'add_component': func, 'get_cabinet_structure': func, ...}
        """
        self.tools = tools

    @abstractmethod
    def can_handle(self, intent: str, context: dict) -> bool:
        """判断该 Skill 是否能处理当前意图"""
        ...

    @abstractmethod
    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        """执行该 Skill，返回操作指令序列"""
        ...

    async def pre_check(self, cabinet_id: int, params: dict) -> bool:
        """执行前校验（可选覆写）"""
        return True

    async def post_check(self, cabinet_id: int, result: SkillResult) -> bool:
        """执行后校验（可选覆写）"""
        return True

    async def rollback(self, cabinet_id: int, params: dict) -> None:
        """回滚操作（可选覆写）"""
        pass
```

### 10.2 Skill 实现示例

#### ShelfSkill（隔板操作）

```python
# skills/shelf_skill.py
class ShelfSkill(BaseSkill):
    skill_id = "add_shelf"
    skill_name = "添加隔板"
    description = "在柜体内部指定位置添加活动隔板，支持单块或多块均匀分布"
    examples = [
        "加一块隔板",
        "在柜子中间加一块隔板",
        "加三块均匀分布的隔板",
        "在高度60厘米处加一块隔板"
    ]

    # 领域规则
    MIN_SHELF_SPACING = 150    # 最小隔板间距(mm)
    DEFAULT_THICKNESS = 18     # 默认隔板厚度(mm)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        cabinet = await self.tools['get_cabinet_structure'](cabinet_id)
        internal_space = self._calc_internal_space(cabinet)

        count = params.get('count', 1)
        target_ratios = params.get('position_ratios', None)

        if target_ratios is None:
            # 均匀分布
            target_ratios = [i / (count + 1) for i in range(1, count + 1)]

        operations = []
        existing_shelves = [c for c in cabinet['components']
                           if c['component_type'] == 'shelf']

        for ratio in target_ratios:
            y_pos = internal_space['y_min'] + ratio * internal_space['y_range']
            # 碰撞检测
            if self._would_overlap(y_pos, existing_shelves, self.MIN_SHELF_SPACING):
                continue

            op = self.tools['add_component'].to_operation(
                cabinet_id=cabinet_id,
                component_type='shelf',
                position_y=y_pos,
                width=internal_space['width'],
                depth=internal_space['depth'],
                height=self.DEFAULT_THICKNESS,
                material=params.get('material'),
                color=params.get('color')
            )
            operations.append(op)
            existing_shelves.append({'position_y': y_pos})

        return SkillResult(
            success=True,
            message=f"已添加 {len(operations)} 块隔板",
            operations=operations
        )
```

#### DoorSkill（门板操作）

```python
# skills/door_skill.py
class DoorSkill(BaseSkill):
    skill_id = "add_doors"
    skill_name = "添加门板"
    description = "添加柜门。支持指定数量、样式（平板/造型/玻璃/百叶）、覆盖范围（全高/上半/下半）"
    examples = [
        "加两扇门",
        "加一扇玻璃门",
        "上面加两扇对开门",
        "换成平板门"
    ]

    # 领域规则
    VALID_STYLES = ['flat', 'panel', 'glass', 'louver']
    DOOR_GAP = 3                # 门缝(mm)
    DEFAULT_HANDLE = 'long'     # 默认拉手样式

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        cabinet = await self.tools['get_cabinet_structure'](cabinet_id)
        count = params.get('count', 1)
        style = params.get('style', 'flat')
        cover_range = params.get('cover_range', 'full')  # full | upper | lower

        if style not in self.VALID_STYLES:
            return SkillResult(success=False, message=f"不支持的门板样式: {style}",
                             operations=[], error="invalid_style")

        # 计算门板区域
        door_zone = self._calc_door_zone(cabinet, cover_range)
        door_width = (cabinet['width'] - (count - 1) * self.DOOR_GAP) / count

        operations = []
        # 先删除旧门板及其关联拉手
        existing_doors = [c for c in cabinet['components'] if c['component_type'] == 'door']
        for door in existing_doors:
            operations.append(self.tools['remove_component'].to_operation(
                cabinet_id=cabinet_id, component_id=door['id']
            ))

        # 创建新门板
        for i in range(count):
            x_pos = -cabinet['width'] / 2 + door_width / 2 + i * (door_width + self.DOOR_GAP)
            op = self.tools['add_component'].to_operation(
                cabinet_id=cabinet_id,
                component_type='door',
                position_x=x_pos,
                position_y=door_zone['y_center'],
                position_z=cabinet['depth'] / 2 + 2,  # 门板在柜体前方
                width=door_width,
                height=door_zone['height'],
                depth=2,  # 门板厚度2mm（3D显示用）
                door_style=style,
                material=params.get('material'),
                color=params.get('color')
            )
            operations.append(op)

            # 添加拉手
            handle_op = self.tools['add_component'].to_operation(
                cabinet_id=cabinet_id,
                component_type='handle',
                parent_component_index=len(operations) - 1,
                handle_style=params.get('handle_style', self.DEFAULT_HANDLE)
            )
            operations.append(handle_op)

        return SkillResult(
            success=True,
            message=f"已添加 {count} 扇{style_zh[style]}门板",
            operations=operations
        )
```

#### ReorganizeLayoutSkill（布局重排）

```python
# skills/layout_skill.py
class ReorganizeLayoutSkill(BaseSkill):
    skill_id = "reorganize_layout"
    skill_name = "重新布局"
    description = "对柜子进行复杂结构调整，如'上面两门下面三抽屉'。自动编排子Skills完成整体布局。"
    examples = [
        "上面加两扇对开门，下面加三个抽屉",
        "重新布局：上半部玻璃门，下半部两个大抽屉",
    ]

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        layout = params['layout_spec']  # 如前端/AI解析的结构化布局描述
        all_operations = []

        for zone in layout['zones']:
            sub_skill = self._resolve_sub_skill(zone['type'])
            if sub_skill:
                sub_params = self._build_sub_params(zone)
                result = await sub_skill.execute(cabinet_id, sub_params, context)
                all_operations.extend(result.operations)

        return SkillResult(
            success=True,
            message=f"布局调整完成",
            operations=all_operations
        )

    def _resolve_sub_skill(self, zone_type: str) -> BaseSkill:
        """根据区域类型解析对应 Skill"""
        mapping = {
            'door': DoorSkill,
            'drawer': DrawerSkill,
            'shelf': ShelfSkill,
        }
        skill_cls = mapping.get(zone_type)
        return skill_cls(self.tools) if skill_cls else None
```

### 10.3 Skill 注册中心

```python
# agent/skill_registry.py
class SkillRegistry:
    """Skills 注册中心 — 管理所有 Skill 的注册、发现与调用"""

    def __init__(self, tools: dict):
        self.tools = tools
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """注册一个 Skill"""
        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Optional[BaseSkill]:
        """按 ID 获取 Skill"""
        return self._skills.get(skill_id)

    def list_all(self) -> list[dict]:
        """获取所有 Skill 的元信息（供前端展示和LLM路由）"""
        return [
            {
                "skill_id": s.skill_id,
                "skill_name": s.skill_name,
                "description": s.description,
                "examples": s.examples,
            }
            for s in self._skills.values()
        ]

    def get_skill_descriptions_for_prompt(self) -> str:
        """生成注入到 System Prompt 的 Skills 描述文本"""
        lines = []
        for s in self._skills.values():
            lines.append(f"- {s.skill_id}: {s.description}")
            lines.append(f"  触发示例: {'; '.join(s.examples[:3])}")
        return "\n".join(lines)

    def match_skill(self, intent: str, context: dict) -> Optional[BaseSkill]:
        """根据用户意图匹配最合适的 Skill（由LLM通过function call选择）"""
        # 实际匹配由 LLM 根据 Skill 描述完成，此处为兜底逻辑
        for skill in self._skills.values():
            if skill.can_handle(intent, context):
                return skill
        return None

    def get_all_skill_tools(self) -> list:
        """获取注册给 DeepAgents Agent 的所有 Skill 入口工具"""
        # 每个 Skill 暴露为一个 Agent Tool（function call）
        return [self._build_skill_tool_schema(s) for s in self._skills.values()]

    def _build_skill_tool_schema(self, skill: BaseSkill) -> dict:
        """将 Skill 转换为 Agent 可调用的工具定义"""
        return {
            "type": "function",
            "function": {
                "name": skill.skill_id,
                "description": skill.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cabinet_id": {"type": "integer"},
                        "params": {"type": "object"},
                    },
                    "required": ["cabinet_id", "params"],
                },
            },
        }
```

### 10.4 Skills 执行流程

```
用户输入自然语言
       │
       ▼
┌──────────────────┐
│  Agent 接收消息    │
│  + 当前柜子上下文  │
│  + 对话历史       │
│  + Skills 描述    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  LLM 意图分析     │
│  选择 Skill(s)   │
└────────┬─────────┘
         │
         ▼  SSE: skill_selected
┌──────────────────┐
│  Skill.execute() │
│  ├── pre_check   │
│  ├── 领域规则计算  │
│  ├── 调用 Tools   │
│  ├── post_check  │
│  └── 生成操作序列  │
└────────┬─────────┘
         │
         ▼  SSE: tool_calls + skill_completed
┌──────────────────┐
│  返回操作指令序列  │
│  (SSE 流式)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  前端编辑引擎     │
│  执行操作指令     │
│  + 约束求解      │
│  + 3D 视图刷新   │
└──────────────────┘
```

### 10.5 Skills 与 Agent 协作模式

**模式一：单一 Skill 调用**
用户意图明确匹配单个 Skill → Agent 直接调用 Skill 入口 → Skill 内部编排多步 Tool 调用。

```
用户："在中间加一块隔板"
  → Agent 选择: add_shelf(count=1, position_ratios=[0.5])
    → Skill 内部: get_cabinet_structure → 计算位置 → add_component
```

**模式二：多 Skill 串联**
用户意图复杂，需多个 Skill 顺序执行 → Agent 编排 Skill 调用链。

```
用户："上面加两扇玻璃门，下面加三个抽屉"
  → Agent 选择: [add_doors, add_drawers]
    → add_doors(count=2, style="glass", cover_range="upper")
    → add_drawers(count=3, cover_range="lower")
```

**模式三：Skill 嵌套**
高层 Skill 内部编排多个子 Skill 完成复杂任务。

```
用户："重新布局，上面两个玻璃对开门，下面两个大抽屉"
  → Agent 选择: reorganize_layout(layout_spec={...})
    → Skill 内部:
      → sub: add_doors(count=2, style="glass", cover_range="upper")
      → sub: add_drawers(count=2, cover_range="lower")
```

---

## 11. 测试策略

### 11.1 测试层级

| 层级 | 测试内容 | 工具 | 覆盖率目标 |
|------|----------|------|-----------|
| 单元测试 - Skills | 每个 Skill 的独立逻辑、领域规则、边界条件 | pytest | ≥ 90% |
| 单元测试 - Services | CRUD 数据服务 | pytest + SQLite in-memory | ≥ 85% |
| 单元测试 - 前端编辑引擎 | 约束求解器、板件工厂、快照管理 | Vitest | ≥ 85% |
| 集成测试 - API | FastAPI 路由端到端测试 | pytest + httpx | ≥ 80% |
| 集成测试 - Agent | Agent + Skills 编排的正确性 | pytest + mock LLM | ≥ 80% |
| E2E测试 | 前端完整用户流程 | Playwright | 核心流程覆盖 |

### 11.2 Skill 单元测试示例

```python
# tests/test_skills/test_shelf_skill.py
class TestShelfSkill:
    async def test_add_single_shelf_middle(self, tools, cabinet):
        skill = ShelfSkill(tools)
        result = await skill.execute(
            cabinet_id=cabinet.id,
            params={'count': 1, 'position_ratios': [0.5]},
            context={}
        )
        assert result.success
        assert len(result.operations) == 1
        assert result.operations[0]['component_type'] == 'shelf'
        # 验证隔板位于柜体中间
        expected_y = cabinet.height / 2
        assert abs(result.operations[0]['position_y'] - expected_y) < 1

    async def test_add_multiple_shelves_uniform(self, tools, cabinet):
        skill = ShelfSkill(tools)
        result = await skill.execute(
            cabinet_id=cabinet.id,
            params={'count': 3},
            context={}
        )
        assert result.success
        assert len(result.operations) == 3

    async def test_shelf_collision_detection(self, tools, cabinet_with_shelves):
        """已有一块隔板在中间，再添加时应跳过重叠位置"""
        skill = ShelfSkill(tools)
        result = await skill.execute(
            cabinet_id=cabinet_with_shelves.id,
            params={'count': 1, 'position_ratios': [0.5]},  # 与已有隔板重叠
            context={}
        )
        assert len(result.operations) == 0  # 重叠，跳过
```

### 11.3 Agent 编排测试示例

```python
# tests/test_ai.py
class TestAgentSkillOrchestration:
    async def test_agent_routes_to_add_shelf(self, agent, cabinet):
        response = await agent.chat(cabinet.id, "在柜子中间加一块隔板")
        assert "add_shelf" in response.skills_used
        assert any(op['component_type'] == 'shelf' for op in response.operations)

    async def test_agent_orchestrates_multi_skills(self, agent, cabinet):
        response = await agent.chat(cabinet.id, "上面加两扇玻璃门，下面加三个抽屉")
        assert set(response.skills_used) == {'add_doors', 'add_drawers'}
        door_ops = [op for op in response.operations if op['component_type'] == 'door']
        drawer_ops = [op for op in response.operations if op['component_type'] == 'drawer']
        assert len(door_ops) >= 2  # 至少2扇门（含拉手可能更多op）
        assert len(drawer_ops) >= 3
```

---

## 12. 开发阶段规划

| 阶段 | 内容 | 里程碑 |
|------|------|--------|
| Phase 1: 基础框架 | 前后端项目骨架搭建、数据库初始化、Three.js 基础渲染 | 能看到默认柜子3D模型 |
| Phase 2: 编辑引擎 | 约束求解器、板件增删改、面板UI、操作历史 | 可视化编辑柜子板件 |
| Phase 3: AI基础 | DeepAgents Agent 接入、基础工具函数、SSE对话流 | 自然语言完成简单编辑 |
| Phase 4: Skills体系 | Skill 基类、Shelf/Door/Drawer Skill 实现、Skill 注册中心 | 自然语言完成结构化编辑 |
| Phase 5: 高级Skills | Layout/Material/Resize Skill、多Skill编排 | AI处理复杂意图 |
| Phase 6: 测试完善 | Skill单元测试、Agent编排测试、前端约束求解测试、E2E | 测试覆盖率达标 |
| Phase 7: 优化上线 | 性能优化、错误处理、UX打磨 | 可演示的完整产品 |

---

## 13. 附录

### 13.1 材质库

| 材质ID | 中文名 | 颜色基准 | 说明 |
|--------|--------|----------|------|
| `wood_oak` | 橡木 | #C49A6C | 浅色木纹 |
| `wood_walnut` | 胡桃木 | #5C3A21 | 深色木纹 |
| `wood_maple` | 枫木 | #E8C99B | 浅黄色木纹 |
| `wood_cherry` | 樱桃木 | #8B4513 | 红棕色木纹 |
| `paint_white` | 白色烤漆 | #FFFFFF | 高光白色 |
| `paint_black` | 黑色烤漆 | #1A1A1A | 哑光黑色 |
| `paint_grey` | 灰色烤漆 | #808080 | 中灰色 |
| `paint_navy` | 深蓝烤漆 | #1B2838 | 深蓝色 |
| `metal_steel` | 不锈钢 | #C0C0C0 | 金属拉丝 |
| `metal_gold` | 金色 | #FFD700 | 金色金属 |
| `glass_clear` | 透明玻璃 | rgba(255,255,255,0.3) | 透明 |
| `glass_frosted` | 磨砂玻璃 | rgba(255,255,255,0.5) | 半透明 |

### 13.2 门板样式

| 样式ID | 中文名 | 说明 |
|--------|--------|------|
| `flat` | 平板门 | 无造型平板 |
| `panel` | 造型门 | 中间凸起面板 |
| `glass` | 玻璃门 | 中间玻璃嵌板 |
| `louver` | 百叶门 | 横向百叶片 |

### 13.3 把手样式

| 样式ID | 中文名 | 说明 |
|--------|--------|------|
| `hidden` | 隐藏把手 | 门板边沿内嵌 |
| `long` | 长条把手 | 竖向长条拉手 |
| `knob` | 圆钮把手 | 圆形小拉手 |