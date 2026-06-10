<script setup lang="ts">
import { useCabinetStore } from '../stores/cabinet';
import { ComponentType, REQUIRED_COMPONENT_TYPES, MATERIAL_NAMES, MATERIAL_COLORS, type MaterialType } from '../types';

const store = useCabinetStore();

function canDelete(type: ComponentType): boolean {
  return !REQUIRED_COMPONENT_TYPES.has(type);
}

function getComponentColor(comp: { color: string | null; material: MaterialType | null }): string {
  if (comp.color) return comp.color;
  const mat = comp.material ?? store.cabinet?.globalMaterial ?? 'wood_oak';
  return MATERIAL_COLORS[mat as MaterialType] ?? '#C49A6C';
}

function getComponentGroup(comp: { componentType: ComponentType }): string {
  const t = comp.componentType;
  if (
    REQUIRED_COMPONENT_TYPES.has(t) ||
    t === ComponentType.BackBoard
  ) return '柜体';
  if (t === ComponentType.Shelf) return '隔板';
  if (t === ComponentType.Door) return '门板';
  if (t === ComponentType.Drawer) return '抽屉';
  return '配件';
}
</script>

<template>
  <div class="property-tab">
    <!-- Cabinet Info -->
    <div v-if="store.cabinet" class="section">
      <h3 class="section-title">柜体信息</h3>
      <div class="prop-grid">
        <label>宽度 (mm)
          <input type="number" v-model.number="store.cabinet.width" @change="store.recalculateBodyBoards(); store.isDirty = true" />
        </label>
        <label>高度 (mm)
          <input type="number" v-model.number="store.cabinet.height" @change="store.recalculateBodyBoards(); store.isDirty = true" />
        </label>
        <label>深度 (mm)
          <input type="number" v-model.number="store.cabinet.depth" @change="store.recalculateBodyBoards(); store.isDirty = true" />
        </label>
        <label>板厚 (mm)
          <input type="number" v-model.number="store.cabinet.boardThickness" @change="store.recalculateBodyBoards(); store.isDirty = true" />
        </label>
      </div>
    </div>

    <!-- Component Tree grouped by type -->
    <div class="section">
      <h3 class="section-title">板件列表 ({{ store.sortedComponents.length }})</h3>
      <div class="component-tree">
        <template v-for="group in ['柜体', '隔板', '门板', '抽屉', '配件']" :key="group">
          <div
            v-if="store.sortedComponents.filter(c => getComponentGroup(c) === group).length > 0"
            class="tree-group"
          >
            <div class="group-label">{{ group }}</div>
            <div
              v-for="comp in store.sortedComponents.filter(c => getComponentGroup(c) === group)"
              :key="comp.id"
              class="tree-item"
              :class="{ selected: store.selectedComponentId === comp.id }"
              @click="store.selectComponent(comp.id)"
            >
              <span
                class="color-dot"
                :style="{ backgroundColor: getComponentColor(comp) }"
              />
              <span class="comp-label">{{ comp.label }}</span>
              <button
                v-if="canDelete(comp.componentType)"
                class="btn-icon"
                @click.stop="store.removeComponent(comp.id)"
                title="删除"
              >
                &times;
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Selected Component Editor -->
    <div v-if="store.selectedComponent && store.cabinet" class="section">
      <h3 class="section-title">编辑: {{ store.selectedComponent.label }}</h3>
      <div class="prop-grid">
        <label>位置 X
          <input type="number" v-model.number="store.selectedComponent.positionX" @change="store.isDirty = true" />
        </label>
        <label>位置 Y
          <input type="number" v-model.number="store.selectedComponent.positionY" @change="store.isDirty = true" />
        </label>
        <label>位置 Z
          <input type="number" v-model.number="store.selectedComponent.positionZ" @change="store.isDirty = true" />
        </label>
        <label>宽度
          <input type="number" v-model.number="store.selectedComponent.width" @change="store.isDirty = true" />
        </label>
        <label>高度
          <input type="number" v-model.number="store.selectedComponent.height" @change="store.isDirty = true" />
        </label>
        <label>深度
          <input type="number" v-model.number="store.selectedComponent.depth" @change="store.isDirty = true" />
        </label>
      </div>
      <div class="prop-grid">
        <label>材质
          <select
            :value="store.selectedComponent.material ?? store.cabinet.globalMaterial"
            @change="store.selectedComponent.material = ($event.target as HTMLSelectElement).value as MaterialType; store.isDirty = true"
          >
            <option v-for="(name, key) in MATERIAL_NAMES" :key="key" :value="key">{{ name }}</option>
          </select>
        </label>
        <label>颜色
          <input
            type="color"
            :value="getComponentColor(store.selectedComponent)"
            @input="store.selectedComponent.color = ($event.target as HTMLInputElement).value; store.isDirty = true"
          />
        </label>
      </div>
      <div class="delete-row">
        <button
          class="btn btn-danger btn-sm"
          :disabled="!canDelete(store.selectedComponent.componentType)"
          @click="store.removeComponent(store.selectedComponent!.id)"
        >
          删除组件
        </button>
      </div>
    </div>

    <!-- Add Components -->
    <div class="section">
      <h3 class="section-title">添加板件</h3>
      <div class="add-buttons">
        <button class="btn btn-sm" @click="store.addComponent(ComponentType.Shelf)">+ 隔板</button>
        <button class="btn btn-sm" @click="store.addComponent(ComponentType.Door)">+ 门板</button>
        <button class="btn btn-sm" @click="store.addComponent(ComponentType.Drawer)">+ 抽屉</button>
        <button class="btn btn-sm" @click="store.addComponent(ComponentType.Leg)">+ 柜脚</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.property-tab {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #aaa;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prop-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}

.prop-grid label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #888;
}

.prop-grid input,
.prop-grid select {
  background: #1a1a2e;
  border: 1px solid #3a3a5a;
  color: #e0e0e0;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.prop-grid input[type="color"] {
  padding: 2px;
  height: 32px;
  cursor: pointer;
}

.component-tree {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.group-label {
  font-size: 11px;
  color: #666;
  padding: 6px 8px 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.tree-item:hover {
  background: #1a1a2e;
}

.tree-item.selected {
  background: #2a2a5a;
  border: 1px solid #7c83ff;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.comp-label {
  flex: 1;
}

.btn-icon {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
}

.btn-icon:hover {
  color: #ef4444;
}

.delete-row {
  margin-top: 8px;
}

.add-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.btn {
  background: #2a2a4a;
  border: 1px solid #3a3a5a;
  color: #e0e0e0;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn:hover:not(:disabled) {
  background: #3a3a5a;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.btn-danger {
  background: #5a2a2a;
  border-color: #7a3a3a;
}

.btn-danger:hover:not(:disabled) {
  background: #7a3a3a;
}
</style>
