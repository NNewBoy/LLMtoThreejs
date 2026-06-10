import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Cabinet, Component, AIOperation } from '../types';
import { ComponentType, REQUIRED_COMPONENT_TYPES } from '../types';
import { BoardFactory } from '../engine/BoardFactory';
import { SnapshotManager } from '../engine/SnapshotManager';
import { ConstraintSolver } from '../engine/ConstraintSolver';

const API_BASE = '/api';

export const useCabinetStore = defineStore('cabinet', () => {
  // State
  const cabinet = ref<Cabinet | null>(null);
  const components = ref<Component[]>([]);
  const selectedComponentId = ref<number | null>(null);
  const snapshotManager = ref(new SnapshotManager());
  const viewMode = ref<'normal' | 'exploded' | 'xray'>('normal');
  const isDirty = ref(false);

  // Computed
  const selectedComponent = computed(() =>
    components.value.find((c) => c.id === selectedComponentId.value) ?? null
  );

  const sortedComponents = computed(() =>
    [...components.value]
      .filter((c) => c.isEnabled)
      .sort((a, b) => a.sortOrder - b.sortOrder)
  );

  const bodyComponents = computed(() =>
    sortedComponents.value.filter((c) =>
      REQUIRED_COMPONENT_TYPES.has(c.componentType) ||
      c.componentType === ComponentType.BackBoard
    )
  );

  const accessoryComponents = computed(() =>
    sortedComponents.value.filter((c) =>
      !REQUIRED_COMPONENT_TYPES.has(c.componentType) &&
      c.componentType !== ComponentType.BackBoard
    )
  );

  // Actions
  async function loadCabinet(id: number): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/cabinets/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cabinet.value = data.cabinet;
      components.value = data.components;
      selectedComponentId.value = null;
      snapshotManager.value.clear();
      isDirty.value = false;
    } catch (err) {
      console.error('Failed to load cabinet:', err);
      // 使用默认柜子数据（开发模式）
      createDefaultCabinet();
    }
  }

  /** 创建默认柜子（用于开发/演示） */
  function createDefaultCabinet(): void {
    cabinet.value = {
      id: 1,
      name: '示例柜子',
      width: 800,
      height: 1200,
      depth: 500,
      boardThickness: 18,
      globalMaterial: 'wood_oak',
      globalColor: '#C49A6C',
    };

    const c = cabinet.value;
    const bodyPlacements = ConstraintSolver.computeBodyBoards(c);
    components.value = bodyPlacements.map((placement, idx) => ({
      id: idx + 1,
      cabinetId: c.id,
      componentType: placement.componentType,
      parentId: null,
      label: placement.label,
      sortOrder: idx,
      width: placement.width,
      height: placement.height,
      depth: placement.depth,
      positionX: placement.positionX,
      positionY: placement.positionY,
      positionZ: placement.positionZ,
      rotationX: 0,
      rotationY: 0,
      rotationZ: 0,
      material: null,
      color: null,
      doorStyle: null,
      handleStyle: null,
      isEnabled: true,
    }));

    isDirty.value = false;
  }

  async function saveCabinet(): Promise<void> {
    if (!cabinet.value) return;
    try {
      const res = await fetch(`${API_BASE}/cabinets/${cabinet.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cabinet: cabinet.value,
          components: components.value,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      isDirty.value = false;
    } catch (err) {
      console.error('Failed to save cabinet:', err);
    }
  }

  function addComponent(type: ComponentType, options?: Partial<Component>): void {
    if (!cabinet.value) return;
    snapshotManager.value.takeSnapshot(cabinet.value, components.value, `添加 ${type}`);
    const data = BoardFactory.createComponentData(type, cabinet.value, options);
    components.value.push(data);
    isDirty.value = true;
  }

  function removeComponent(id: number): void {
    const comp = components.value.find((c) => c.id === id);
    if (!comp) return;
    if (REQUIRED_COMPONENT_TYPES.has(comp.componentType)) return; // 必选板件不可删除

    if (!cabinet.value) return;
    snapshotManager.value.takeSnapshot(cabinet.value, components.value, `删除 ${comp.label}`);
    components.value = components.value.filter((c) => c.id !== id);

    // 删除门板时自动删除关联拉手
    if (comp.componentType === ComponentType.Door) {
      components.value = components.value.filter(
        (c) => !(c.componentType === ComponentType.Handle && c.parentId === id)
      );
    }

    if (selectedComponentId.value === id) {
      selectedComponentId.value = null;
    }
    isDirty.value = true;
  }

  function updateComponent(id: number, changes: Partial<Component>): void {
    const idx = components.value.findIndex((c) => c.id === id);
    if (idx === -1) return;

    if (!cabinet.value) return;
    snapshotManager.value.takeSnapshot(cabinet.value, components.value, `修改 ${components.value[idx].label}`);

    components.value[idx] = { ...components.value[idx], ...changes };
    isDirty.value = true;
  }

  function selectComponent(id: number | null): void {
    selectedComponentId.value = id;
  }

  function undo(): void {
    const snapshot = snapshotManager.value.undo();
    if (!snapshot) return;
    if (cabinet.value) {
      cabinet.value = snapshot.cabinet;
    }
    components.value = snapshot.components;
    selectedComponentId.value = null;
  }

  function redo(): void {
    const snapshot = snapshotManager.value.redo();
    if (!snapshot) return;
    if (cabinet.value) {
      cabinet.value = snapshot.cabinet;
    }
    components.value = snapshot.components;
    selectedComponentId.value = null;
  }

  function applyAIOperations(operations: AIOperation[]): void {
    if (!cabinet.value) return;
    snapshotManager.value.takeSnapshot(cabinet.value, components.value, 'AI操作');

    for (const op of operations) {
      switch (op.action) {
        case 'add':
          if (op.componentType) {
            const data = BoardFactory.createComponentData(
              op.componentType,
              cabinet.value,
              op.data
            );
            if (op.label) data.label = op.label;
            components.value.push(data);
          }
          break;
        case 'remove':
          if (op.componentId) {
            components.value = components.value.filter((c) => c.id !== op.componentId);
          }
          break;
        case 'update':
          if (op.componentId && op.data) {
            const idx = components.value.findIndex((c) => c.id === op.componentId);
            if (idx !== -1) {
              components.value[idx] = { ...components.value[idx], ...op.data };
            }
          }
          break;
        case 'replace':
          if (op.data) {
            components.value = components.value.map((c) => ({ ...c, ...op.data }));
          }
          break;
      }
    }
    isDirty.value = true;
  }

  /** 重新计算柜体板件（柜体尺寸变化时） */
  function recalculateBodyBoards(): void {
    if (!cabinet.value) return;
    const placements = ConstraintSolver.computeBodyBoards(cabinet.value);
    for (const placement of placements) {
      const existing = components.value.find(
        (c) => c.componentType === placement.componentType && c.isEnabled
      );
      if (existing) {
        existing.width = placement.width;
        existing.height = placement.height;
        existing.depth = placement.depth;
        existing.positionX = placement.positionX;
        existing.positionY = placement.positionY;
        existing.positionZ = placement.positionZ;
      }
    }
  }

  return {
    // State
    cabinet,
    components,
    selectedComponentId,
    snapshotManager,
    viewMode,
    isDirty,
    // Computed
    selectedComponent,
    sortedComponents,
    bodyComponents,
    accessoryComponents,
    // Actions
    loadCabinet,
    createDefaultCabinet,
    saveCabinet,
    addComponent,
    removeComponent,
    updateComponent,
    selectComponent,
    undo,
    redo,
    applyAIOperations,
    recalculateBodyBoards,
  };
});
