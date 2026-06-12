import type { Cabinet, Component, CabinetSnapshot } from '../types';

/**
 * 操作快照管理器 — 支持撤销/重做（时间线方案）
 *
 * 使用 history 数组 + currentIndex 指针管理状态。
 * takeSnapshot 在操作**后**调用，保存操作后的状态。
 * undo 回退到上一个快照，redo 前进到下一个快照。
 */
export class SnapshotManager {
  private history: CabinetSnapshot[] = [];
  private currentIndex: number = -1;
  private maxHistory = 50;

  /** 保存当前状态快照（应在操作完成后调用） */
  takeSnapshot(cabinet: Cabinet, components: Component[], description: string = ''): void {
    const snapshot: CabinetSnapshot = {
      cabinet: JSON.parse(JSON.stringify(cabinet)),
      components: JSON.parse(JSON.stringify(components)),
      timestamp: Date.now(),
      description,
    };

    // 新操作：截断 currentIndex 之后的 redo 历史
    this.history = this.history.slice(0, this.currentIndex + 1);

    this.history.push(snapshot);
    this.currentIndex = this.history.length - 1;

    // 超出上限时移除最早的快照
    if (this.history.length > this.maxHistory) {
      this.history.shift();
      this.currentIndex--;
    }
  }

  /** 撤销：回退到上一个快照，返回该状态 */
  undo(): CabinetSnapshot | null {
    if (this.currentIndex <= 0) return null;
    this.currentIndex--;
    return this.history[this.currentIndex];
  }

  /** 重做：前进到下一个快照，返回该状态 */
  redo(): CabinetSnapshot | null {
    if (this.currentIndex >= this.history.length - 1) return null;
    this.currentIndex++;
    return this.history[this.currentIndex];
  }

  canUndo(): boolean {
    return this.currentIndex > 0;
  }

  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  clear(): void {
    this.history = [];
    this.currentIndex = -1;
  }
}
