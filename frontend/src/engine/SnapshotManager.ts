import type { Cabinet, Component, CabinetSnapshot } from '../types';

/**
 * 操作快照管理器 — 支持撤销/重做
 * SPEC2 section 4.1.4
 */
export class SnapshotManager {
  private undoStack: CabinetSnapshot[] = [];
  private redoStack: CabinetSnapshot[] = [];
  private maxHistory = 50;

  /** 记录当前状态快照 */
  takeSnapshot(cabinet: Cabinet, components: Component[], description: string = ''): void {
    const snapshot: CabinetSnapshot = {
      cabinet: JSON.parse(JSON.stringify(cabinet)),
      components: JSON.parse(JSON.stringify(components)),
      timestamp: Date.now(),
      description,
    };
    this.undoStack.push(snapshot);
    if (this.undoStack.length > this.maxHistory) {
      this.undoStack.shift();
    }
    // 新操作后清空重做栈
    this.redoStack = [];
  }

  /** 撤销：返回上一个状态 */
  undo(): CabinetSnapshot | null {
    const snapshot = this.undoStack.pop();
    if (!snapshot) return null;
    this.redoStack.push(snapshot);
    return this.undoStack.length > 0 ? this.undoStack[this.undoStack.length - 1] : null;
  }

  /** 重做：返回下一个状态 */
  redo(): CabinetSnapshot | null {
    const snapshot = this.redoStack.pop();
    if (!snapshot) return null;
    this.undoStack.push(snapshot);
    return snapshot;
  }

  canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  clear(): void {
    this.undoStack = [];
    this.redoStack = [];
  }
}
