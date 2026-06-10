<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { useCabinetStore } from '../stores/cabinet';
import { BoardFactory } from '../engine/BoardFactory';

const emit = defineEmits<{ 'update:fps': [value: number] }>();

const containerRef = ref<HTMLDivElement>();
const store = useCabinetStore();

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let raycaster: THREE.Raycaster;
let mouse: THREE.Vector2;
let animationId: number;
let frameCount = 0;
let lastFpsTime = 0;

const componentMeshes = new Map<number, THREE.Mesh>();
let selectionOutline: THREE.LineSegments | null = null;

const SELECTION_COLOR = 0xffff00;

function initScene() {
  if (!containerRef.value) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a2e);

  const w = containerRef.value.clientWidth;
  const h = containerRef.value.clientHeight;

  // FOV 50, camera at (1200, 800, 1200) looking at (0, 600, 0)
  camera = new THREE.PerspectiveCamera(50, w / h, 1, 10000);
  camera.position.set(1200, 800, 1200);
  camera.lookAt(0, 600, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  containerRef.value.appendChild(renderer.domElement);

  // Lights: Ambient 0.4, Directional 0.8 with shadows, Hemisphere 0.3
  scene.add(new THREE.AmbientLight(0xffffff, 0.4));

  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(500, 1000, 500);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 2048;
  dirLight.shadow.mapSize.height = 2048;
  dirLight.shadow.camera.near = 1;
  dirLight.shadow.camera.far = 5000;
  dirLight.shadow.camera.left = -1500;
  dirLight.shadow.camera.right = 1500;
  dirLight.shadow.camera.top = 1500;
  dirLight.shadow.camera.bottom = -1500;
  scene.add(dirLight);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 0.3));

  // Ground plane for shadow receiving
  const groundGeo = new THREE.PlaneGeometry(4000, 4000);
  const groundMat = new THREE.ShadowMaterial({ opacity: 0.3 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -1;
  ground.receiveShadow = true;
  scene.add(ground);

  // GridHelper(2000, 20) on XZ plane
  scene.add(new THREE.GridHelper(2000, 20, 0x444466, 0x2a2a4a));

  // OrbitControls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(0, 600, 0);
  controls.minDistance = 200;
  controls.maxDistance = 5000;
  controls.update();

  // Raycaster
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();
  renderer.domElement.addEventListener('click', onCanvasClick);

  // Resize
  const ro = new ResizeObserver(() => {
    if (!containerRef.value) return;
    const cw = containerRef.value.clientWidth;
    const ch = containerRef.value.clientHeight;
    camera.aspect = cw / ch;
    camera.updateProjectionMatrix();
    renderer.setSize(cw, ch);
  });
  ro.observe(containerRef.value);
}

function onCanvasClick(event: MouseEvent) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const meshes = Array.from(componentMeshes.values());
  const intersects = raycaster.intersectObjects(meshes);

  if (intersects.length > 0) {
    const hit = intersects[0].object as THREE.Mesh;
    store.selectComponent(hit.userData.componentId as number);
  } else {
    store.selectComponent(null);
  }
}

function rebuildMeshes() {
  if (!store.cabinet) return;

  for (const [, mesh] of componentMeshes) {
    scene.remove(mesh);
    mesh.geometry.dispose();
    if (mesh.material instanceof THREE.Material) mesh.material.dispose();
  }
  componentMeshes.clear();
  clearSelectionOutline();

  for (const comp of store.sortedComponents) {
    const mesh = BoardFactory.createMesh(comp, store.cabinet);
    scene.add(mesh);
    componentMeshes.set(comp.id, mesh);
  }
}

function updateMeshes() {
  if (!store.cabinet) return;

  const currentIds = new Set(store.sortedComponents.map((c) => c.id));

  // Remove deleted
  for (const [id, mesh] of componentMeshes) {
    if (!currentIds.has(id)) {
      scene.remove(mesh);
      mesh.geometry.dispose();
      if (mesh.material instanceof THREE.Material) mesh.material.dispose();
      componentMeshes.delete(id);
    }
  }

  // Add / update
  for (const comp of store.sortedComponents) {
    const existing = componentMeshes.get(comp.id);
    if (existing) {
      BoardFactory.updateMesh(existing, comp, store.cabinet);
    } else {
      const mesh = BoardFactory.createMesh(comp, store.cabinet);
      scene.add(mesh);
      componentMeshes.set(comp.id, mesh);
    }
  }
}

function updateSelectionHighlight() {
  clearSelectionOutline();
  if (store.selectedComponentId === null) return;
  const mesh = componentMeshes.get(store.selectedComponentId);
  if (!mesh) return;

  const edges = new THREE.EdgesGeometry(mesh.geometry);
  const lineMat = new THREE.LineBasicMaterial({ color: SELECTION_COLOR, linewidth: 2 });
  selectionOutline = new THREE.LineSegments(edges, lineMat);
  selectionOutline.position.copy(mesh.position);
  selectionOutline.rotation.copy(mesh.rotation);
  selectionOutline.scale.copy(mesh.scale);
  scene.add(selectionOutline);
}

function clearSelectionOutline() {
  if (selectionOutline) {
    scene.remove(selectionOutline);
    selectionOutline.geometry.dispose();
    (selectionOutline.material as THREE.Material).dispose();
    selectionOutline = null;
  }
}

/** Exploded view: offset each component outward from center by 100mm */
function applyExplodedView() {
  for (const comp of store.sortedComponents) {
    const mesh = componentMeshes.get(comp.id);
    if (!mesh) continue;

    const dir = new THREE.Vector3(comp.positionX, comp.positionY - 600, comp.positionZ);
    if (dir.length() < 1) {
      dir.set(0, 1, 0);
    } else {
      dir.normalize();
    }

    const offset = dir.multiplyScalar(100);
    mesh.position.set(
      comp.positionX + offset.x,
      comp.positionY + offset.y,
      comp.positionZ + offset.z
    );
  }
}

function resetPositions() {
  for (const comp of store.sortedComponents) {
    const mesh = componentMeshes.get(comp.id);
    if (!mesh) continue;
    mesh.position.set(comp.positionX, comp.positionY, comp.positionZ);
  }
}

/** X-ray mode: non-selected get opacity=0.3, transparent=true */
function applyXrayMode() {
  for (const comp of store.sortedComponents) {
    const mesh = componentMeshes.get(comp.id);
    if (!mesh) continue;
    const mat = mesh.material as THREE.MeshStandardMaterial;
    if (!mat || !('opacity' in mat)) continue;

    if (comp.id === store.selectedComponentId) {
      mat.transparent = false;
      mat.opacity = 1;
    } else {
      mat.transparent = true;
      mat.opacity = 0.3;
    }
    mat.needsUpdate = true;
  }
}

function resetMaterialOpacity() {
  for (const [, mesh] of componentMeshes) {
    const mat = mesh.material as THREE.MeshStandardMaterial;
    if (!mat || !('opacity' in mat)) continue;
    const compId = mesh.userData.componentId as number;
    const comp = store.sortedComponents.find((c) => c.id === compId);
    const isGlass = comp && (comp.material === 'glass' || comp.doorStyle === 'glass');
    if (isGlass) {
      mat.transparent = true;
      mat.opacity = 0.3;
    } else {
      mat.transparent = false;
      mat.opacity = 1;
    }
    mat.needsUpdate = true;
  }
}

function animate() {
  animationId = requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);

  frameCount++;
  const now = performance.now();
  if (now - lastFpsTime >= 1000) {
    emit('update:fps', frameCount);
    frameCount = 0;
    lastFpsTime = now;
  }
}

// Watchers
watch(
  () => store.sortedComponents,
  () => {
    updateMeshes();
    updateSelectionHighlight();
  },
  { deep: true }
);

watch(
  () => store.selectedComponentId,
  () => {
    updateSelectionHighlight();
    if (store.viewMode === 'xray') applyXrayMode();
  }
);

watch(
  () => store.viewMode,
  (mode) => {
    resetPositions();
    resetMaterialOpacity();
    if (mode === 'exploded') applyExplodedView();
    else if (mode === 'xray') applyXrayMode();
  }
);

onMounted(async () => {
  await nextTick();
  initScene();
  rebuildMeshes();
  animate();
});

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId);
  renderer?.dispose();
  for (const [, mesh] of componentMeshes) {
    mesh.geometry.dispose();
    if (mesh.material instanceof THREE.Material) mesh.material.dispose();
  }
  componentMeshes.clear();
});
</script>

<template>
  <div ref="containerRef" class="three-canvas" />
</template>

<style scoped>
.three-canvas {
  width: 100%;
  height: 100%;
  cursor: grab;
}

.three-canvas:active {
  cursor: grabbing;
}
</style>
