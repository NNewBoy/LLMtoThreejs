import type { Cabinet, Component, BoardPlacement, BoundingBox } from '../types';
import { ComponentType } from '../types';

/**
 * 约束求解器 — SPEC2 section 4.1.3
 * 前端维护板件之间的约束关系，自动计算位置和尺寸
 */
export class ConstraintSolver {
  /**
   * 根据柜体尺寸计算必选板件（顶/底/左/右/背板）位置
   * 约束规则:
   *   1. 顶板Y = 柜体高度 - 顶板厚度
   *   2. 底板Y = 0
   *   3. 左侧板X = -柜体宽度/2 + 左侧板厚度/2
   *   4. 右侧板X = 柜体宽度/2 - 右侧板厚度/2
   *   5. 背板Z = -柜体深度/2 + 背板厚度/2
   */
  static computeBodyBoards(cabinet: Cabinet): BoardPlacement[] {
    const { width, height, depth, boardThickness: t } = cabinet;

    // 侧板高度 = 柜体高度 - 顶板厚度 - 底板厚度
    const sideBoardHeight = height - t * 2;
    // 侧板深度 = 柜体深度
    const sideBoardDepth = depth;
    // 顶/底板宽度 = 柜体宽度
    const topBottomWidth = width;
    // 顶/底板深度 = 柜体深度
    const topBottomDepth = depth;
    // 背板宽度 = 柜体宽度 - 2 * 侧板厚度
    const backBoardWidth = width - t * 2;
    // 背板高度 = 柜体高度 - 顶板厚度 - 底板厚度
    const backBoardHeight = sideBoardHeight;

    return [
      {
        componentType: ComponentType.TopBoard,
        width: topBottomWidth,
        height: t,
        depth: topBottomDepth,
        positionX: 0,
        positionY: height - t / 2,
        positionZ: 0,
        label: '顶板',
      },
      {
        componentType: ComponentType.BottomBoard,
        width: topBottomWidth,
        height: t,
        depth: topBottomDepth,
        positionX: 0,
        positionY: t / 2,
        positionZ: 0,
        label: '底板',
      },
      {
        componentType: ComponentType.LeftBoard,
        width: t,
        height: sideBoardHeight,
        depth: sideBoardDepth,
        positionX: -width / 2 + t / 2,
        positionY: t + sideBoardHeight / 2,
        positionZ: 0,
        label: '左侧板',
      },
      {
        componentType: ComponentType.RightBoard,
        width: t,
        height: sideBoardHeight,
        depth: sideBoardDepth,
        positionX: width / 2 - t / 2,
        positionY: t + sideBoardHeight / 2,
        positionZ: 0,
        label: '右侧板',
      },
      {
        componentType: ComponentType.BackBoard,
        width: backBoardWidth,
        height: backBoardHeight,
        depth: t,
        positionX: 0,
        positionY: t + backBoardHeight / 2,
        positionZ: -depth / 2 + t / 2,
        label: '背板',
      },
    ];
  }

  /**
   * 计算柜体内部可用空间
   */
  static getInternalSpace(cabinet: Cabinet): BoundingBox {
    const t = cabinet.boardThickness;
    const xMin = -cabinet.width / 2 + t;
    const xMax = cabinet.width / 2 - t;
    const yMin = t;
    const yMax = cabinet.height - t;
    const zMin = -cabinet.depth / 2 + t;
    const zMax = cabinet.depth / 2;

    return {
      xMin,
      xMax,
      yMin,
      yMax,
      zMin,
      zMax,
      width: xMax - xMin,
      height: yMax - yMin,
      depth: zMax - zMin,
    };
  }

  /**
   * 计算隔板位置
   * 约束:
   *   - 隔板Y范围: 底板厚度 < Y < 顶板底部
   *   - 隔板宽度 = 柜体内部宽度
   *   - 隔板深度 ≤ 柜体内部深度
   */
  static computeShelfPlacement(
    cabinet: Cabinet,
    count: number = 1,
    targetY?: number
  ): BoardPlacement[] {
    const internal = this.getInternalSpace(cabinet);
    const t = cabinet.boardThickness;
    const placements: BoardPlacement[] = [];

    if (count <= 0) return placements;

    if (count === 1 && targetY !== undefined) {
      // 单块隔板放在指定高度
      const clampedY = Math.max(internal.yMin + t, Math.min(targetY, internal.yMax - t));
      placements.push({
        componentType: ComponentType.Shelf,
        width: internal.width,
        height: t,
        depth: internal.depth,
        positionX: 0,
        positionY: clampedY,
        positionZ: 0,
        label: '隔板',
      });
    } else {
      // 多块隔板均匀分布
      const usableHeight = internal.height - t;
      const gap = usableHeight / (count + 1);
      for (let i = 1; i <= count; i++) {
        const y = internal.yMin + gap * i;
        placements.push({
          componentType: ComponentType.Shelf,
          width: internal.width,
          height: t,
          depth: internal.depth,
          positionX: 0,
          positionY: y,
          positionZ: 0,
          label: `隔板 ${i}`,
        });
      }
    }

    return placements;
  }

  /**
   * 计算门板位置
   * 约束:
   *   - 门板宽度之和 ≤ 柜体宽度
   *   - 门板高度 ≤ 柜体高度
   *   - 门板位于柜体正面 (Z = depth/2 + 门板厚度/2)
   */
  static computeDoorPlacement(
    cabinet: Cabinet,
    count: number,
    style: string = 'flat',
    _coverRange: string = 'full'
  ): BoardPlacement[] {
    const t = cabinet.boardThickness;
    const doorThickness = t; // 门板厚度与柜体板厚一致
    const doorWidth = cabinet.width / count;
    const doorHeight = _coverRange === 'full' ? cabinet.height : cabinet.height / 2;
    const doorYBase = _coverRange === 'lower' ? 0 : cabinet.height - doorHeight;

    const placements: BoardPlacement[] = [];

    for (let i = 0; i < count; i++) {
      const x = -cabinet.width / 2 + doorWidth / 2 + doorWidth * i;
      placements.push({
        componentType: ComponentType.Door,
        width: doorWidth - (count > 1 ? 2 : 0), // 多扇门留缝隙
        height: doorHeight,
        depth: doorThickness,
        positionX: x,
        positionY: doorYBase + doorHeight / 2,
        positionZ: cabinet.depth / 2 + doorThickness / 2,
        label: `门板 ${i + 1} (${style})`,
      });
    }

    return placements;
  }

  /**
   * 计算抽屉位置
   * 约束:
   *   - 抽屉总高度之和 ≤ 柜体可用高度
   *   - 抽屉宽度 = 柜体内部宽度
   */
  static computeDrawerPlacement(
    cabinet: Cabinet,
    count: number,
    startY: number = 0
  ): BoardPlacement[] {
    const internal = this.getInternalSpace(cabinet);
    const t = cabinet.boardThickness;
    const drawerDepth = internal.depth - 20; // 抽屉深度略小于内部深度
    const drawerGap = 4; // 抽屉间隙

    // 可用高度：从 startY 到柜体顶部内部
    const availableHeight = internal.yMax - startY - t;
    const drawerHeight = (availableHeight - drawerGap * (count - 1)) / count;

    const placements: BoardPlacement[] = [];

    for (let i = 0; i < count; i++) {
      const y = startY + t + drawerHeight / 2 + (drawerHeight + drawerGap) * i;
      placements.push({
        componentType: ComponentType.Drawer,
        width: internal.width,
        height: drawerHeight,
        depth: drawerDepth,
        positionX: 0,
        positionY: y,
        positionZ: 5, // 抽屉略靠前
        label: `抽屉 ${i + 1}`,
      });
    }

    return placements;
  }

  /**
   * 检测板件是否与其他板件重叠（AABB碰撞检测）
   */
  static checkOverlap(component: Component, allComponents: Component[]): boolean {
    const a = {
      xMin: component.positionX - component.width / 2,
      xMax: component.positionX + component.width / 2,
      yMin: component.positionY - component.height / 2,
      yMax: component.positionY + component.height / 2,
      zMin: component.positionZ - component.depth / 2,
      zMax: component.positionZ + component.depth / 2,
    };

    for (const other of allComponents) {
      if (other.id === component.id || !other.isEnabled) continue;

      const b = {
        xMin: other.positionX - other.width / 2,
        xMax: other.positionX + other.width / 2,
        yMin: other.positionY - other.height / 2,
        yMax: other.positionY + other.height / 2,
        zMin: other.positionZ - other.depth / 2,
        zMax: other.positionZ + other.depth / 2,
      };

      const overlap =
        a.xMin < b.xMax && a.xMax > b.xMin &&
        a.yMin < b.yMax && a.yMax > b.yMin &&
        a.zMin < b.zMax && a.zMax > b.zMin;

      if (overlap) return true;
    }

    return false;
  }
}
