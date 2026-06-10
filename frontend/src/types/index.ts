/** 板件类型枚举 */
export enum ComponentType {
  TopBoard = 'top_board',
  BottomBoard = 'bottom_board',
  LeftBoard = 'left_board',
  RightBoard = 'right_board',
  BackBoard = 'back_board',
  Shelf = 'shelf',
  Door = 'door',
  Drawer = 'drawer',
  Handle = 'handle',
  Leg = 'leg',
  Baseboard = 'baseboard',
}

/** 必选板件类型（不可删除） */
export const REQUIRED_COMPONENT_TYPES = new Set<ComponentType>([
  ComponentType.TopBoard,
  ComponentType.BottomBoard,
  ComponentType.LeftBoard,
  ComponentType.RightBoard,
]);

/** 门板样式 */
export type DoorStyle = 'flat' | 'shaker' | 'glass' | 'louver';

/** 把手样式 */
export type HandleStyle = 'hidden' | 'bar' | 'knob';

/** 材质类型 */
export type MaterialType = 'wood_oak' | 'wood_walnut' | 'wood_pine' | 'paint_white' | 'paint_black' | 'paint_gray' | 'glass' | 'metal';

/** 颜色映射表 (SPEC2 附录 13.1) */
export const MATERIAL_COLORS: Record<MaterialType, string> = {
  wood_oak: '#C49A6C',
  wood_walnut: '#5C4033',
  wood_pine: '#DEB887',
  paint_white: '#F5F5F5',
  paint_black: '#2C2C2C',
  paint_gray: '#808080',
  glass: '#E0F0FF',
  metal: '#A8A8A8',
};

/** 材质中文名 */
export const MATERIAL_NAMES: Record<MaterialType, string> = {
  wood_oak: '白橡木',
  wood_walnut: '胡桃木',
  wood_pine: '松木',
  paint_white: '白色烤漆',
  paint_black: '黑色烤漆',
  paint_gray: '灰色烤漆',
  glass: '玻璃',
  metal: '金属',
};

/** 柜子数据 */
export interface Cabinet {
  id: number;
  name: string;
  width: number;   // mm
  height: number;  // mm
  depth: number;   // mm
  boardThickness: number; // mm, default 18
  globalMaterial: MaterialType;
  globalColor: string;
}

/** 板件/组件数据 */
export interface Component {
  id: number;
  cabinetId: number;
  componentType: ComponentType;
  parentId: number | null;
  label: string;
  sortOrder: number;
  width: number;
  height: number;
  depth: number;
  positionX: number;
  positionY: number;
  positionZ: number;
  rotationX: number;
  rotationY: number;
  rotationZ: number;
  material: MaterialType | null;
  color: string | null;
  doorStyle: DoorStyle | null;
  handleStyle: HandleStyle | null;
  isEnabled: boolean;
}

/** 约束求解器返回的板件位置/尺寸 */
export interface BoardPlacement {
  componentType: ComponentType;
  width: number;
  height: number;
  depth: number;
  positionX: number;
  positionY: number;
  positionZ: number;
  label: string;
}

/** 包围盒 */
export interface BoundingBox {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  zMin: number;
  zMax: number;
  width: number;
  height: number;
  depth: number;
}

/** AI聊天消息 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  skillId?: string;
  skillName?: string;
}

/** AI操作 */
export interface AIOperation {
  action: 'add' | 'remove' | 'update' | 'replace';
  componentType?: ComponentType;
  componentId?: number;
  data?: Partial<Component>;
  label?: string;
}

/** Skill信息 */
export interface SkillInfo {
  skillId: string;
  skillName: string;
  progress: string;
}

/** 操作快照 */
export interface CabinetSnapshot {
  cabinet: Cabinet;
  components: Component[];
  timestamp: number;
  description: string;
}
