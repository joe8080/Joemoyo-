import React, {useLayoutEffect, useMemo, useRef} from 'react';
import {useCurrentFrame} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import * as THREE from 'three';

export const PLATE_FRAMES = 600; // 20 s seamless loop
const PITCH = 1.2;
const LOOP = 12.0; // = 10 racks, so the pattern repeats exactly
const NR = 72; // racks per side
const LEDS_PER_RACK = 24;
const hash = (a: number, b: number) => {
  let h = (Math.imul(a, 374761393) + Math.imul(b, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
};

const Hall: React.FC<{f: number}> = ({f}) => {
  const phase = f / PLATE_FRAMES; // 0..1 loop
  const racksRef = useRef<THREE.InstancedMesh>(null!);
  const ledRef = useRef<THREE.InstancedMesh>(null!);
  const refRef = useRef<THREE.InstancedMesh>(null!);
  const guideRef = useRef<THREE.InstancedMesh>(null!);
  const stripRef = useRef<THREE.InstancedMesh>(null!);
  const trayRef = useRef<THREE.InstancedMesh>(null!);
  const edgeRef = useRef<THREE.InstancedMesh>(null!);

  const ledBase = useMemo(() => {
    const arr: {m: THREE.Matrix4; base: THREE.Color; id: number}[] = [];
    let id = 0;
    for (let side = 0; side < 2; side++) {
      for (let k = 0; k < NR; k++) {
        const zc = 3.6 - k * PITCH;
        const kk = k % 10;
        for (let c = 0; c < 3; c++) {
          for (let r = 0; r < 8; r++) {
            const sgn = side === 0 ? -1 : 1;
            const m = new THREE.Matrix4().makeTranslation(sgn * 1.495, 0.35 + r * 0.26, zc + (c - 1) * 0.3);
            const hh = hash(kk * 97 + c * 13 + r, side + 7);
            const base = new THREE.Color(hh > 0.93 ? '#f2b84b' : hh > 0.985 ? '#f0716b' : '#2dd4bf');
            arr.push({m, base, id: kk * 1000 + side * 500 + c * 50 + r});
            id++;
          }
        }
      }
    }
    return arr;
  }, []);

  useLayoutEffect(() => {
    // racks (static)
    const tmp = new THREE.Matrix4();
    let i = 0;
    for (let side = 0; side < 2; side++) {
      for (let k = 0; k < NR; k++) {
        const zc = 3.6 - k * PITCH;
        const sgn = side === 0 ? -1 : 1;
        tmp.makeTranslation(sgn * 2.0, 1.2, zc);
        racksRef.current.setMatrixAt(i, tmp);
        tmp.makeTranslation(sgn * 1.505, 2.43, zc);
        edgeRef.current.setMatrixAt(i, tmp);
        i++;
      }
    }
    racksRef.current.instanceMatrix.needsUpdate = true;
    edgeRef.current.instanceMatrix.needsUpdate = true;
    // LEDs
    const mir = new THREE.Matrix4();
    ledBase.forEach((l, idx) => {
      ledRef.current.setMatrixAt(idx, l.m);
      const e = l.m.elements; mir.makeTranslation(e[12], -e[13], e[14]);
      refRef.current.setMatrixAt(idx, mir);
    });
    ledRef.current.instanceMatrix.needsUpdate = true;
    refRef.current.instanceMatrix.needsUpdate = true;
    tmp.makeTranslation(-1.2, 0.012, -30); guideRef.current.setMatrixAt(0, tmp);
    tmp.makeTranslation(1.2, 0.012, -30); guideRef.current.setMatrixAt(1, tmp);
    guideRef.current.instanceMatrix.needsUpdate = true;
    // ceiling strips + trays
    for (let k = 0; k < NR; k++) {
      const zc = 3.6 - k * PITCH;
      tmp.makeTranslation(0, 3.05, zc);
      stripRef.current.setMatrixAt(k, tmp);
      tmp.makeTranslation(0, 2.78, zc);
      trayRef.current.setMatrixAt(k, tmp);
    }
    stripRef.current.instanceMatrix.needsUpdate = true;
    trayRef.current.instanceMatrix.needsUpdate = true;
  }, []);

  // LED blink state (periodic so the loop is seamless): 40 steps per loop
  useLayoutEffect(() => {
    const step = Math.floor(phase * 40) % 40;
    const col = new THREE.Color();
    ledBase.forEach((l, idx) => {
      const on = hash(l.id, step) > 0.62 ? 1 : hash(l.id, 99) > 0.82 ? 0.55 : 0.07;
      col.copy(l.base).multiplyScalar(on * 1.6);
      ledRef.current.setColorAt(idx, col);
      col.multiplyScalar(0.28);
      refRef.current.setColorAt(idx, col);
    });
    ledRef.current.instanceColor!.needsUpdate = true;
    refRef.current.instanceColor!.needsUpdate = true;
  }, [phase]);

  const camZ = -phase * LOOP;
  const sway = Math.sin(phase * Math.PI * 2);
  const camX = sway * 0.14;
  const camY = 1.55 + Math.sin(phase * Math.PI * 4) * 0.03;
  const {camera} = useThree();
  camera.position.set(camX, camY, camZ);
  camera.lookAt(camX * 0.4, 1.5, camZ - 9);
  camera.updateProjectionMatrix();
  return (
    <>
      <ambientLight intensity={0.9} color="#7f96c8" />
      <pointLight position={[camX, 2.2, camZ - 1]} intensity={9} distance={9} color="#9fd4ff" />
      <fogExp2 attach="fog" args={['#04060c', 0.055]} />
      <instancedMesh ref={racksRef} args={[undefined as any, undefined as any, NR * 2]}>
        <boxGeometry args={[1.0, 2.4, 1.0]} />
        <meshStandardMaterial color="#121c36" roughness={0.55} metalness={0.45} />
      </instancedMesh>
      <instancedMesh ref={edgeRef} args={[undefined as any, undefined as any, NR * 2]}>
        <boxGeometry args={[0.02, 0.03, 0.98]} />
        <meshBasicMaterial color="#2dd4bf" toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={ledRef} args={[undefined as any, undefined as any, ledBase.length]}>
        <boxGeometry args={[0.012, 0.05, 0.11]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={refRef} args={[undefined as any, undefined as any, ledBase.length]}>
        <boxGeometry args={[0.012, 0.05, 0.11]} />
        <meshBasicMaterial toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={guideRef} args={[undefined as any, undefined as any, 2]}>
        <boxGeometry args={[0.03, 0.01, 120]} />
        <meshBasicMaterial color="#2dd4bf" toneMapped={false} transparent opacity={0.55} />
      </instancedMesh>
      <instancedMesh ref={stripRef} args={[undefined as any, undefined as any, NR]}>
        <boxGeometry args={[0.18, 0.03, 0.9]} />
        <meshBasicMaterial color="#cfe9ff" toneMapped={false} />
      </instancedMesh>
      <instancedMesh ref={trayRef} args={[undefined as any, undefined as any, NR]}>
        <boxGeometry args={[1.2, 0.06, 1.0]} />
        <meshStandardMaterial color="#0a1122" roughness={0.7} metalness={0.4} />
      </instancedMesh>
      <mesh position={[0, 0, -30]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[6, 120]} />
        <meshStandardMaterial color="#070d1b" roughness={0.35} metalness={0.7} transparent opacity={0.82} />
      </mesh>
      <mesh position={[0, 3.3, -30]} rotation={[Math.PI / 2, 0, 0]}>
        <planeGeometry args={[6, 120]} />
        <meshStandardMaterial color="#060a14" roughness={0.9} />
      </mesh>
    </>
  );
};

export const Plate: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <div style={{width: 1280, height: 720, background: '#04060c'}}>
      <ThreeCanvas width={1280} height={720} camera={{position: [0, 1.55, 0], fov: 62}} gl={{antialias: false, powerPreference: 'high-performance'}}>
        <color attach="background" args={['#04060c']} />
        <Hall f={f % PLATE_FRAMES} />
      </ThreeCanvas>
    </div>
  );
};
