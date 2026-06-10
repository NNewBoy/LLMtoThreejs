# CabinetCraft Pro

单柜板件级 3D 在线编辑器 — 支持可视化面板编辑与自然语言 AI 编辑。

## 功能概览

- **3D 实时渲染**：Three.js 渲染柜子所有板件，支持旋转/缩放/平移
- **板件级编辑**：点击选中板件，修改位置、尺寸、材质、颜色
- **约束求解**：板件之间自动维护 12 条约束规则，拖拽时自动适配
- **撤销/重做**：Ctrl+Z / Ctrl+Y，操作快照管理
- **爆炸视图 / 透视模式**：一键展开柜子查看内部结构
- **AI 自然语言编辑**：输入"加两块隔板"、"换成玻璃门"等自然语言，Agent 自动执行
- **Skills 架构**：7 个领域 Skill 封装柜子设计操作，支持编排和嵌套

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Three.js + Pinia |
| 后端 | FastAPI + SQLAlchemy + SQLite + OpenAI SDK |
| AI Agent | LLM Function Calling + Skills 体系 |
| 通信 | REST API + SSE (Server-Sent Events) |

## 项目结构

```
LLMtoThreejs/
├── backend/                    # Python 后端
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置（数据库、LLM、CORS）
│   ├── database.py             # SQLAlchemy 引擎
│   ├── models/                 # ORM 模型 (4 表)
│   ├── schemas/                # Pydantic 请求/响应模型
│   ├── services/               # 业务逻辑层
│   ├── routers/                # API 路由
│   ├── agent/                  # LLM Agent 层
│   ├── skills/                 # 7 个领域 Skill
│   └── .env                    # 环境变量配置
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── engine/             # 编辑引擎（约束求解、板件工厂、快照）
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── components/         # Vue 组件（3D画布、属性面板、AI对话）
│   │   └── types/              # TypeScript 类型定义
│   └── vite.config.ts          # Vite 配置（含后端代理）
│
└── SPEC2.md                    # 软件规格说明书
```

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（首次）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置 LLM_API_KEY（可选，不设置则使用关键词回退模式）

# 启动服务
python main.py
```

后端启动后：
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs (Swagger UI)
- 健康检查：http://localhost:8000/health

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:5173

### 3. 启用 AI 功能（可选）

编辑 `backend/.env`：

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

支持任何 OpenAI 兼容接口（如 DeepSeek、通义千问等），修改 `LLM_BASE_URL` 即可。

不配置 API Key 时，AI 对话会使用关键词匹配回退模式，支持简单的指令识别。

## API 接口

### 柜子管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cabinets` | 列出所有柜子 |
| POST | `/api/cabinets` | 创建新柜子（含默认板件） |
| GET | `/api/cabinets/{id}` | 获取柜子详情（含所有板件） |
| PUT | `/api/cabinets/{id}` | 更新柜子属性 |
| DELETE | `/api/cabinets/{id}` | 删除柜子 |
| PUT | `/api/cabinets/{id}/size` | 调整柜体尺寸 |

### 板件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cabinets/{id}/components` | 获取所有板件 |
| POST | `/api/cabinets/{id}/components` | 添加板件 |
| PUT | `/api/cabinets/{id}/components/{cid}` | 更新板件 |
| DELETE | `/api/cabinets/{id}/components/{cid}` | 删除板件 |

### AI 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | 发送自然语言指令（SSE 流式响应） |
| GET | `/api/ai/skills` | 获取可用 Skills 列表 |

### 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

## 前端操作指南

### 3D 视图

| 操作 | 说明 |
|------|------|
| 鼠标左键拖拽 | 旋转视角 |
| 鼠标右键拖拽 | 平移视角 |
| 滚轮 | 缩放 |
| 点击板件 | 选中（黄色高亮边框） |
| 点击空白 | 取消选中 |

### 键盘快捷键

| 按键 | 功能 |
|------|------|
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| Delete | 删除选中板件（必选板件不可删除） |

### 视图模式

| 模式 | 说明 |
|------|------|
| 普通视图 | 默认渲染模式 |
| 爆炸视图 | 所有板件沿法线方向展开，查看内部结构 |
| 透视模式 | 非选中板件半透明（opacity=0.3） |

### 右侧面板

**属性编辑 Tab：**
- 柜子整体属性（名称、尺寸）
- 板件列表（按类型分组：柜体、隔板、门板、抽屉、配件）
- 选中板件属性编辑（位置、尺寸、材质、颜色）
- 添加板件按钮组

**AI 对话 Tab：**
- 输入自然语言指令
- Skill 执行进度卡片
- 操作确认/拒绝

### AI 对话示例

```
"在柜子中间加一块隔板"
"加三块均匀分布的隔板"
"上面加两扇玻璃对开门，下面加三个抽屉"
"把所有隔板改成胡桃木材质"
"把柜子加高20厘米"
"这个柜子有几块隔板？"
```

## Skills 体系

| Skill ID | 名称 | 功能 |
|----------|------|------|
| `add_shelf` | 添加隔板 | 指定位置或均匀分布添加隔板 |
| `add_doors` | 添加门板 | 指定数量、样式、覆盖范围添加门板 |
| `add_drawers` | 添加抽屉 | 指定区域添加抽屉组 |
| `change_material` | 批量换材质 | 按类型批量更换材质/颜色 |
| `query_structure` | 查询结构 | 获取柜子结构描述和板件统计 |
| `adjust_cabinet_size` | 调整尺寸 | 修改柜体尺寸并联动更新板件 |
| `reorganize_layout` | 重新布局 | 复杂结构调整，编排子 Skills |

## 数据库

使用 SQLite，数据库文件位于 `backend/cabinet_craft.db`，启动时自动创建。

### 表结构

- **cabinets**：柜子主表（名称、尺寸、默认材质）
- **components**：板件/组件表（类型、位置、尺寸、材质、样式）
- **operation_history**：操作历史（含 JSON 快照）
- **ai_chat_history**：AI 对话历史

## 约束规则

前端约束求解器维护板件之间的 12 条约束关系：

1. 顶板 Y = 柜体高度 - 顶板厚度
2. 底板 Y = 0
3. 左侧板 X = -宽度/2 + 厚度/2
4. 右侧板 X = 宽度/2 - 厚度/2
5. 背板 Z = -深度/2 + 厚度/2
6. 隔板 Y 范围：底板厚度 < Y < 顶板底部
7. 隔板宽度 = 柜体内部宽度
8. 隔板深度 ≤ 柜体内部深度
9. 门板宽度之和 ≤ 柜体宽度
10. 门板高度 ≤ 柜体高度
11. 抽屉总高度 ≤ 柜体可用高度
12. 抽屉宽度 = 柜体内部宽度

## 材质库

| ID | 中文名 | 颜色 |
|----|--------|------|
| `wood_oak` | 橡木 | #C49A6C |
| `wood_walnut` | 胡桃木 | #5C3A21 |
| `wood_maple` | 枫木 | #E8C99B |
| `wood_cherry` | 樱桃木 | #8B4513 |
| `paint_white` | 白色烤漆 | #FFFFFF |
| `paint_black` | 黑色烤漆 | #1A1A1A |
| `paint_grey` | 灰色烤漆 | #808080 |
| `glass_clear` | 透明玻璃 | rgba(255,255,255,0.3) |

## 开发

### 后端开发

```bash
cd backend
python main.py  # 热重载模式，修改代码自动重启
```

### 前端开发

```bash
cd frontend
npm run dev  # Vite HMR，修改代码自动刷新
```

### 构建生产版本

```bash
cd frontend
npm run build  # 输出到 frontend/dist/
```

## License

MIT
