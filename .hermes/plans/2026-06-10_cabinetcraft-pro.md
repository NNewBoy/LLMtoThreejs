# CabinetCraft Pro — Implementation Plan

> Based on SPEC2.md — Single cabinet panel-level 3D editor with Agent + Skills

## Goal
Build a complete web-based 3D cabinet editor with Vue 3 + Three.js frontend and FastAPI + LLM Agent backend.

## Architecture
- **Frontend**: Vue 3 + TypeScript + Vite + Three.js + Pinia
- **Backend**: FastAPI + SQLAlchemy + SQLite + DeepAgents (OpenAI-compatible LLM)
- **Communication**: REST API + SSE for AI chat streaming

## Stats
- Backend: 38 Python files, ~2700 lines
- Frontend: 13 TS/Vue files, ~1170 lines
- Total: ~3870 lines of working code
- Delegated to Claude Code (v2.1.90) in 3 print-mode sessions

## Phases

### Phase 1: Backend Foundation ✅ COMPLETED
- [x] Task 1.1: Project scaffolding + dependencies (venv, requirements.txt)
- [x] Task 1.2: Database models (Cabinet, Component, OperationHistory, AIChatHistory) — SQLAlchemy 2.0 style with Mapped/mapped_column
- [x] Task 1.3: Pydantic v2 schemas (CabinetCreate/Update/Response, ComponentCreate/Update/Response, UnifiedResponse)
- [x] Task 1.4: Database session + config (pydantic-settings, SQLite with FK pragma)
- [x] Task 1.5: Cabinet + Component CRUD services (CabinetService.create_default computes body board positions per constraint rules)
- [x] Task 1.6: API routes (cabinets, components, history) — unified response format {success, data, error}
- [x] Task 1.7: Main FastAPI app + CORS + lifespan table creation

### Phase 2: Backend Skills + Agent ✅ COMPLETED
- [x] Task 2.1: Skill base class + SkillResult (ABC with can_handle, execute, pre_check, post_check, rollback)
- [x] Task 2.2: Skill implementations — 7 skills:
  - ShelfSkill (add_shelf): position_ratios, collision detection, MIN_SHELF_SPACING=150mm
  - DoorSkill (add_doors): styles (flat/panel/glass/louver), cover_range, auto-handle creation
  - DrawerSkill (add_drawers): count, start/end_ratio, handle creation
  - MaterialSkill (change_material): batch material/color change by component type
  - QuerySkill (query_structure): human-readable cabinet description + stats
  - ResizeSkill (adjust_cabinet_size): dimension update with body board recalc
  - ReorganizeLayoutSkill (reorganize_layout): sub-skill orchestration for complex layouts
- [x] Task 2.3: Skill registry (register, list_all, get_skill_descriptions_for_prompt, get_all_skill_tools with OpenAI function-call schemas)
- [x] Task 2.4: Agent tools — 8 atomic functions (add_component, remove_component, update_component, get_cabinet_structure, get_component, list_components, update_cabinet_size, get_snapshot_description)
- [x] Task 2.5: Agent + System Prompt (CabinetAgent with OpenAI async client, function calling, fallback keyword matching when no API key)
- [x] Task 2.6: AI service + SSE streaming endpoint (POST /api/ai/chat with EventSourceResponse, GET /api/ai/skills)
- [ ] Task 2.7: Backend tests (not yet implemented)

### Phase 3: Frontend Foundation ✅ COMPLETED
- [x] Task 3.1: Vue 3 + Vite + TS scaffolding (npm create vite, deps: three, pinia)
- [x] Task 3.2: Three.js basic scene + cabinet rendering (scene, camera at 1200/800/1200, lights: ambient 0.4 + directional 0.8 + hemisphere 0.3, PCFSoftShadowMap, ground plane, GridHelper)
- [x] Task 3.3: Board mesh factory + materials (BoardFactory: MeshStandardMaterial for wood/paint, MeshPhysicalMaterial for glass with transmission=0.8, metal with metalness=0.8)
- [x] Task 3.4: OrbitControls + raycasting + selection (click-to-select with EdgesGeometry yellow outline, ResizeObserver for responsive canvas)

### Phase 4: Frontend Editing Engine ✅ COMPLETED
- [x] Task 4.1: Constraint solver — ConstraintSolver with all 12 rules from SPEC2 4.1.3:
  - computeBodyBoards, computeShelfPlacement, computeDoorPlacement, computeDrawerPlacement
  - getInternalSpace, checkOverlap (AABB collision)
- [x] Task 4.2: Board factory (BoardFactory.createComponentData + createMesh + updateMesh)
- [x] Task 4.3: Snapshot manager (SnapshotManager with undo/redo stacks)
- [x] Task 4.4: Pinia stores:
  - cabinet store: state (cabinet, components, selectedComponentId, viewMode, isDirty), actions (loadCabinet, saveCabinet, addComponent, removeComponent, updateComponent, selectComponent, undo, redo, applyAIOperations, recalculateBodyBoards)
  - chat store: SSE streaming with skill progress tracking, pending operations confirm/reject

### Phase 5: Frontend UI ✅ COMPLETED
- [x] Task 5.1: App layout + header + status bar (editable cabinet name, save/undo/redo buttons, FPS display, keyboard shortcuts Ctrl+Z/Y/Delete)
- [x] Task 5.2: Right panel (PropertyTab with component tree grouped by type, position/size/material editors)
- [x] Task 5.3: Add component panel (buttons for shelf, door, drawer, leg)
- [x] Task 5.4: View modes (exploded view: offset 100mm along normal; xray: non-selected opacity=0.3)
- [x] Task 5.5: AI chat tab + SSE integration (message bubbles, skill progress card, operation confirm/reject, input with Enter key)

### Phase 6: Integration + Polish ✅ CODE COMPLETE
- [x] Task 6.1: Frontend-backend API integration (fetch calls with /api proxy, unified response parsing)
- [x] Task 6.2: AI chat end-to-end flow (SSE event parsing, skill_selected/skill_executing/skill_completed/message/done events)
- [x] Task 6.3: Error handling (try/catch in stores, system messages for errors, fallback when no API key)
- [ ] Task 6.4: Final testing (not yet run)

## How to Run

### Backend
```bash
cd backend
venv\Scripts\activate     # Windows
python main.py            # → http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm run dev               # → http://localhost:5173
```

### AI Features
Set `LLM_API_KEY` in `backend/.env` to enable LLM-powered natural language editing.
Without API key, agent falls back to keyword matching for simple commands.

## File Inventory

### Backend (38 files)
```
backend/
├── main.py, config.py, database.py, requirements.txt, .env
├── models/     __init__.py, cabinet.py, component.py, operation_history.py, ai_chat.py
├── schemas/    __init__.py, cabinet.py, component.py, history.py, ai.py, common.py
├── services/   __init__.py, cabinet_service.py, component_service.py, history_service.py, ai_service.py
├── routers/    __init__.py, cabinets.py, components.py, history.py, ai.py
├── agent/      __init__.py, agent.py, tools.py, prompts.py, skill_registry.py
├── skills/     __init__.py, base.py, shelf_skill.py, door_skill.py, drawer_skill.py,
│               material_skill.py, query_skill.py, resize_skill.py, layout_skill.py
└── venv/       (Python virtual environment with all deps)
```

### Frontend (13 source files)
```
frontend/src/
├── main.ts, App.vue
├── types/          index.ts
├── engine/         ConstraintSolver.ts, BoardFactory.ts, SnapshotManager.ts
├── stores/         cabinet.ts, chat.ts
└── components/     ThreeCanvas.vue, RightPanel.vue, PropertyTab.vue, AITab.vue
```

## Delegation Strategy
Each phase delegated to Claude Code (v2.1.90) as focused print-mode tasks:
- Session 1: Backend foundation (models, schemas, services, routes) — timed out at 600s but completed all files
- Session 2: Frontend (scaffold, engine, Three.js, UI components) — timed out but completed all files
- Session 3: Skills + Agent (7 skills, agent, AI service, SSE endpoint) — timed out but completed all files

## Remaining Work
- [ ] Backend unit tests (pytest)
- [ ] Frontend unit tests (Vitest)
- [ ] E2E tests (Playwright)
- [ ] Texture images for wood materials
- [ ] Backend .env with real LLM API key for AI features testing
