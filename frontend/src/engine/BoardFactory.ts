import * as THREE from 'three';
import type { Cabinet, Component } from '../types';
import { ComponentType, MATERIAL_COLORS, type MaterialType } from '../types';
import { ConstraintSolver } from './ConstraintSolver';

/** 获取组件的实际材质（如无独立材质则继承全局） */
function resolveMaterial(component: Component, cabinet: Cabinet): MaterialType {
  return component.material ?? cabinet.globalMaterial;
}

/** 获取组件的实际颜色（如无独立颜色则基于材质查表） */
function resolveColor(component: Component, cabinet: Cabinet): string {
  if (component.color) return component.color;
  const mat = resolveMaterial(component, cabinet);
  return MATERIAL_COLORS[mat] ?? cabinet.globalColor;
}

let nextId = -1; // 临时ID，后端会分配真实ID

export class BoardFactory {
  /**
   * 根据类型和柜体数据创建 Component 数据对象
   */
  static createComponentData(
    type: ComponentType,
    cabinet: Cabinet,
    options?: Partial<Component>
  ): Component {
    const placement = this.getDefaultPlacement(type, cabinet, options);

    return {
      id: nextId--,
      cabinetId: cabinet.id,
      componentType: type,
      parentId: null,
      label: placement.label,
      sortOrder: this.getSortOrder(type),
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
      doorStyle: type === ComponentType.Door ? 'flat' : null,
      handleStyle: type === ComponentType.Handle ? 'hidden' : null,
      isEnabled: true,
      ...options,
    };
  }

  /**
   * 根据 Component 数据创建 Three.js Mesh
   */
  static createMesh(component: Component, cabinet: Cabinet): THREE.Mesh {
    const geometry = new THREE.BoxGeometry(
      component.width,
      component.height,
      component.depth
    );

    const material = this.createMaterial(component, cabinet);

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(
      component.positionX,
      component.positionY,
      component.positionZ
    );
    mesh.rotation.set(
      component.rotationX,
      component.rotationY,
      component.rotationZ
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.name = `component_${component.id}`;
    mesh.userData = { componentId: component.id, componentType: component.componentType };

    return mesh;
  }

  /**
   * 更新已有 Mesh 的几何和材质
   */
  static updateMesh(mesh: THREE.Mesh, component: Component, cabinet: Cabinet): void {
    // 更新几何
    const newGeometry = new THREE.BoxGeometry(
      component.width,
      component.height,
      component.depth
    );
    mesh.geometry.dispose();
    mesh.geometry = newGeometry;

    // 更新位置和旋转
    mesh.position.set(
      component.positionX,
      component.positionY,
      component.positionZ
    );
    mesh.rotation.set(
      component.rotationX,
      component.rotationY,
      component.rotationZ
    );

    // 更新材质
    const oldMaterial = mesh.material;
    if (oldMaterial instanceof THREE.Material) {
      oldMaterial.dispose();
    }
    mesh.material = this.createMaterial(component, cabinet);

    mesh.name = `component_${component.id}`;
    mesh.userData = { componentId: component.id, componentType: component.componentType };
  }

  /**
   * 创建材质
   * - MeshStandardMaterial 用于不透明板件（木板、烤漆板）
   * - MeshPhysicalMaterial 用于玻璃等透明材质
   */
  private static createMaterial(component: Component, cabinet: Cabinet): THREE.Material {
    const matType = resolveMaterial(component, cabinet);
    const color = resolveColor(component, cabinet);

    if (matType === 'glass' || component.doorStyle === 'glass') {
      return new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: 0.3,
        roughness: 0.05,
        metalness: 0,
        transmission: 0.8,
        thickness: 2,
        side: THREE.DoubleSide,
      });
    }

    if (matType === 'metal') {
      return new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        roughness: 0.3,
        metalness: 0.8,
        side: THREE.DoubleSide,
      });
    }

    // 木材和烤漆
    const isWood = matType.startsWith('wood_');
    return new THREE.MeshStandardMaterial({
      color: new THREE.Color(color),
      roughness: isWood ? 0.7 : 0.3,
      metalness: isWood ? 0.0 : 0.1,
      side: THREE.DoubleSide,
    });
  }

  /** 获取组件类型的默认位置 */
  private static getDefaultPlacement(
    type: ComponentType,
    cabinet: Cabinet,
    options?: Partial<Component>
  ) {
    const t = cabinet.boardThickness;

    switch (type) {
      case ComponentType.TopBoard:
        return {
          width: cabinet.width,
          height: t,
          depth: cabinet.depth,
          positionX: 0,
          positionY: cabinet.height - t / 2,
          positionZ: 0,
          label: '顶板',
        };
      case ComponentType.BottomBoard:
        return {
          width: cabinet.width,
          height: t,
          depth: cabinet.depth,
          positionX: 0,
          positionY: t / 2,
          positionZ: 0,
          label: '底板',
        };
      case ComponentType.LeftBoard:
        return {
          width: t,
          height: cabinet.height - t * 2,
          depth: cabinet.depth,
          positionX: -cabinet.width / 2 + t / 2,
          positionY: t + (cabinet.height - t * 2) / 2,
          positionZ: 0,
          label: '左侧板',
        };
      case ComponentType.RightBoard:
        return {
          width: t,
          height: cabinet.height - t * 2,
          depth: cabinet.depth,
          positionX: cabinet.width / 2 - t / 2,
          positionY: t + (cabinet.height - t * 2) / 2,
          positionZ: 0,
          label: '右侧板',
        };
      case ComponentType.BackBoard: {
        const bH = cabinet.height - t * 2;
        return {
          width: cabinet.width - t * 2,
          height: bH,
          depth: t,
          positionX: 0,
          positionY: t + bH / 2,
          positionZ: -cabinet.depth / 2 + t / 2,
          label: '背板',
        };
      }
      case ComponentType.Shelf:
        return ConstraintSolver.computeShelfPlacement(cabinet, 1, options?.positionY)[0] ?? {
          width: 0, height: 0, depth: 0, positionX: 0, positionY: 0, positionZ: 0, label: '隔板',
        };
      case ComponentType.Door:
        return ConstraintSolver.computeDoorPlacement(cabinet, 1, options?.doorStyle ?? 'flat')[0] ?? {
          width: 0, height: 0, depth: 0, positionX: 0, positionY: 0, positionZ: 0, label: '门板',
        };
      case ComponentType.Drawer:
        return ConstraintSolver.computeDrawerPlacement(cabinet, 1, options?.positionY ?? 0)[0] ?? {
          width: 0, height: 0, depth: 0, positionX: 0, positionY: 0, positionZ: 0, label: '抽屉',
        };
      case ComponentType.Handle: {
        // 把手默认在门板前面中间
        const doorZ = cabinet.depth / 2 + t + 2;
        return {
          width: 80,
          height: 12,
          depth: 12,
          positionX: 0,
          positionY: cabinet.height / 2,
          positionZ: doorZ,
          label: '拉手',
        };
      }
      case ComponentType.Leg:
        return {
          width: 40,
          height: 100,
          depth: 40,
          positionX: 0,
          positionY: -50,
          positionZ: 0,
          label: '柜脚',
        };
      case ComponentType.Baseboard:
        return {
          width: cabinet.width,
          height: 80,
          depth: t,
          positionX: 0,
          positionY: 40,
          positionZ: cabinet.depth / 2 + t / 2,
          label: '踢脚线',
        };
      default:
        return {
          width: t,
          height: t,
          depth: t,
          positionX: 0,
          positionY: 0,
          positionZ: 0,
          label: '未知',
        };
    }
  }

  private static getSortOrder(type: ComponentType): number {
    const order: Record<string, number> = {
      top_board: 0,
      bottom_board: 1,
      left_board: 2,
      right_board: 3,
      back_board: 4,
      shelf: 10,
      door: 20,
      drawer: 30,
      handle: 40,
      leg: 50,
      baseboard: 55,
    };
    return order[type] ?? 99;
  }
}
