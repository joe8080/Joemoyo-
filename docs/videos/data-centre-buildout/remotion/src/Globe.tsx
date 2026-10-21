import React, {useMemo} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';
import {feature} from 'topojson-client';
// @ts-ignore
import land from 'world-atlas/land-110m.json';
import sites from './data/sites.json';
import {A, clamp, eo, pr, sp} from './ui';

const R = 2;
const ll = (lat: number, lon: number, r = R) => {
  const la = (lat * Math.PI) / 180, lo = (lon * Math.PI) / 180;
  return new THREE.Vector3(r * Math.cos(la) * Math.sin(lo), r * Math.sin(la), r * Math.cos(la) * Math.cos(lo));
};

const landGeo = (() => {
  const f: any = feature(land as any, (land as any).objects.land);
  const pts: number[] = [];
  const geoms: any[] = f.type === 'FeatureCollection' ? f.features.map((x: any) => x.geometry) : [f.geometry];
  const pushRing = (ring: number[][]) => {
    for (let i = 0; i < ring.length - 1; i++) {
      const a = ll(ring[i][1], ring[i][0], R * 1.002), b = ll(ring[i + 1][1], ring[i + 1][0], R * 1.002);
      pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
    }
  };
  geoms.forEach((g) => {
    if (g.type === 'Polygon') g.coordinates.forEach(pushRing);
    if (g.type === 'MultiPolygon') g.coordinates.forEach((p: any) => p.forEach(pushRing));
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return geo;
})();

const graticule = (() => {
  const pts: number[] = [];
  for (let lat = -60; lat <= 60; lat += 30) for (let lon = -180; lon < 180; lon += 4) { const a = ll(lat, lon, R * 1.001), b = ll(lat, lon + 4, R * 1.001); pts.push(a.x, a.y, a.z, b.x, b.y, b.z); }
  for (let lon = -180; lon < 180; lon += 30) for (let lat = -80; lat < 80; lat += 4) { const a = ll(lat, lon, R * 1.001), b = ll(lat + 4, lon, R * 1.001); pts.push(a.x, a.y, a.z, b.x, b.y, b.z); }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return geo;
})();

const Pillars: React.FC<{t: number; fps: number}> = ({t, fps}) => {
  const up = new THREE.Vector3(0, 1, 0);
  const items = useMemo(() => (sites as any[]).map((s, i) => {
    const n = ll(s[0], s[1], 1).normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(up, n);
    return {n, q, planned: s[2], oper: s[3], i, lat: s[0], lon: s[1]};
  }), []);
  return (
    <>
      {items.map((it) => {
        const k = 0.0072;
        const hp = k * Math.sqrt(it.planned) * 1.0;
        const ho = it.oper > 0 ? k * Math.sqrt(it.oper) * 1.0 : 0;
        const grow = sp(t, A.q3_plan + (it.i % 20) * 0.05 + 0.15 * (1 - Math.min(1, it.planned / 3000)), fps, 20, 90);
        const growO = sp(t, A.q3_op + (it.i % 14) * 0.04, fps, 20, 90);
        const w = 0.028 + 0.00055 * Math.sqrt(it.planned);
        const hP = Math.max(0.0001, hp * grow);
        const hO = Math.max(0.0001, ho * growO);
        const pos = it.n.clone().multiplyScalar(R + hP / 2);
        const posO = it.n.clone().multiplyScalar(R + hO / 2);
        return (
          <group key={it.i}>
            <mesh position={[pos.x, pos.y, pos.z]} quaternion={it.q} scale={[w, hP, w]}>
              <boxGeometry args={[1, 1, 1]} />
              <meshBasicMaterial color="#f2b84b" transparent opacity={0.55} toneMapped={false} />
            </mesh>
            {ho > 0 && (
              <mesh position={[posO.x, posO.y, posO.z]} quaternion={it.q} scale={[w * 0.62, hO, w * 0.62]}>
                <boxGeometry args={[1, 1, 1]} />
                <meshBasicMaterial color="#2dd4bf" toneMapped={false} />
              </mesh>
            )}
          </group>
        );
      })}
    </>
  );
};

export const Globe: React.FC<{a: number; b: number}> = ({a, b}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const appear = eo(pr(t, a, 1.2));
  // rotation: US at start -> Europe/Gulf later
  const lon0 = -96, lon1 = 20;
  const drift = pr(t, A.q3_30, 10);
  const lon = lon0 + (lon1 - lon0) * (0.3 * pr(t, a, 6) + 0.7 * drift * drift * (3 - 2 * drift)) + (t - a) * 1.2;
  const rotY = (-lon * Math.PI) / 180;
  const tilt = (0.42 - 0.12 * pr(t, A.q3_30, 8));
  const zoom = 14.4 - 0.9 * eo(pr(t, a, 6));
  return (
    <div style={{position: 'absolute', inset: 0, opacity: appear}}>
      <ThreeCanvas width={1920} height={1080} camera={{position: [0, 0, zoom], fov: 34}} gl={{antialias: true}}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[3, 2, 4]} intensity={1.3} color="#aecbff" />
        <group position={[-2.7, -0.5, 0]} rotation={[tilt, 0, 0]}>
          <group rotation={[0, rotY, 0]}>
            <mesh>
              <sphereGeometry args={[R * 0.998, 64, 48]} />
              <meshStandardMaterial color="#0a1630" roughness={0.9} metalness={0.1} emissive="#071026" emissiveIntensity={0.9} />
            </mesh>
            <lineSegments geometry={graticule}>
              <lineBasicMaterial color="#6f8fd8" transparent opacity={0.14} />
            </lineSegments>
            <lineSegments geometry={landGeo}>
              <lineBasicMaterial color="#59b9ff" transparent opacity={0.85} />
            </lineSegments>
            <Pillars t={t} fps={fps} />
          </group>
          <mesh scale={1.12}>
            <sphereGeometry args={[R, 48, 32]} />
            <meshBasicMaterial color="#2a6bff" transparent opacity={0.07} side={THREE.BackSide} />
          </mesh>
        </group>
      </ThreeCanvas>
    </div>
  );
};
