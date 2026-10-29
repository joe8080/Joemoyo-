// Everything that is a function of time: word beats, the orbit simulation, the
// sim clock, poses, camera, shake and depth-of-field. Pure + deterministic, so
// every Remotion render tab computes exactly the same thing.
import {SPR} from './sprites';

export const FPS = 60;
export const DUR = 21;
export const NF = DUR * FPS;
export const VO_AT = 0.1; // voice placed at 0.1 s; all beats below already include it

// Word beats (ElevenLabs Scribe word starts + VO_AT)
export const T = {
	sun: 1.86,
	fifty: 2.74,
	mars: 5.62,
	basically: 6.74,
	earth: 7.54,
	zoom: 8.06,
	your: 10.34,
	rocket: 10.5,
	missing: 12.98,
	fall: 13.94,
	cancel: 15.46,
	nasa: 17.14,
	venus: 18.82,
	brake: 19.54,
} as const;

// Pose swaps + cuts
export const SW = {
	worried: 2.72,
	brace: 7.85,
	windup: 10.18,
	release: 10.5,
	closeIn: 13.02,
	closeOut: 13.85,
	cheer: 20.28,
} as const;

// ---------------------------------------------------------------- world
export const ZP = 1000; // Earth plane: Earth, guy, rocket, Venus, orbit
export const ZS = 3000; // Sun
export const ZM = 2200; // Mars
export const ZST = 9000; // stars

export const O = {x: 540, y: -560}; // orbit centre (the Sun sits on it)
export const RE = 2420; // Earth orbit radius = 1 sim unit
export const EARTH_R = 380;
export const HEAD_R = 150;
export const SUN_R = 1350; // total radius incl. rays
export const VENUS_R = 380;
export const S_A = {x: 720, y: -1170}; // Sun's own spot in the opening shot
export const M_A = {x: -263, y: 1048}; // Mars, opening shot
export const M_W = {x: -1905, y: -3829}; // Mars, wide shot (top-left)
export const E0 = {x: O.x, y: O.y + RE};

export type V = {x: number; y: number};
export type Cam = {x: number; y: number; z: number};

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
export const mixV = (a: V, b: V, u: number): V => ({x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u)});
export const easeInOutCubic = (u: number) => {
	u = clamp(u);
	return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
};
export const easeInOutSine = (u: number) => -(Math.cos(Math.PI * clamp(u)) - 1) / 2;
export const easeOutCubic = (u: number) => 1 - Math.pow(1 - clamp(u), 3);
export const easeOutBack = (u: number, s = 2.2) => {
	u = clamp(u);
	const c3 = s + 1;
	return 1 + c3 * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2);
};
// 0 -> 1 pop with overshoot, then back to 0 at the end (for things that pop on and off)
export const popOnOff = (t: number, on: number, off: number, d = 0.16) =>
	t < on || t > off + d ? 0 : t < on + d ? easeOutBack((t - on) / d) : t < off ? 1 : 1 - easeInOutCubic((t - off) / d);
export const kOf = (camZ: number, Z = ZP) => 1000 / (Z - camZ);
export const zOfK = (k: number) => ZP - 1000 / k;
// damped spring kick: 0 before t0, rings and settles after
export const spring = (t: number, t0: number, decay = 8, freq = 30) =>
	t < t0 ? 0 : Math.exp(-(t - t0) * decay) * Math.cos((t - t0) * freq);

// ---------------------------------------------------------------- orbit sim
// Units: Earth orbit radius 1, GM 1 (Earth: 1 rad per unit of sim time tau).
// Screen y points down; Earth starts at the bottom and moves right (sideways).
const wu = SPR.windup;
const sWind = HEAD_R / wu.head[2];
// rocket centre in the (mirrored) wind-up pose, relative to Earth centre, world px
export const HAND: V = {
	x: -(wu.rocket.c[0] - wu.feet[0]) * sWind,
	y: -EARTH_R + 22 + (wu.rocket.c[1] - wu.feet[1]) * sWind,
};
export const ROCKET_SCALE = (wu.rocket.len * sWind) / SPR.rocket.redLen; // world px per sprite px
export const WIND_ROCKET_ANGLE = -wu.rocket.angle; // mirrored

const DT = 0.0005;
type Sim = {tau0: number; x: number[]; y: number[]; vx: number[]; vy: number[]; hit: boolean};
const TL = 0.8;
const Q = 0.3;
const ANG = (-150 * Math.PI) / 180;

function simulate(burn: number[] | null, brake: number[] | null, tauMax: number): Sim {
	let x = Math.sin(TL) + HAND.x / RE;
	let y = Math.cos(TL) + HAND.y / RE;
	let vx = Math.cos(TL) + Q * Math.cos(ANG);
	let vy = -Math.sin(TL) + Q * Math.sin(ANG);
	const s: Sim = {tau0: TL, x: [x], y: [y], vx: [vx], vy: [vy], hit: false};
	const acc = (px: number, py: number, qx: number, qy: number, th: number) => {
		const r = Math.hypot(px, py);
		let ax = -px / (r * r * r);
		let ay = -py / (r * r * r);
		if (th) {
			const sp = Math.hypot(qx, qy);
			ax -= (th * qx) / sp;
			ay -= (th * qy) / sp;
		}
		return [ax, ay];
	};
	for (let i = 0; TL + i * DT < tauMax; i++) {
		const t = TL + i * DT;
		let th = 0;
		if (burn && t >= burn[0] && t < burn[1]) th = burn[2];
		if (brake && t >= brake[0] && t < brake[1]) th = brake[2];
		const k1v = [vx, vy];
		const k1a = acc(x, y, vx, vy, th);
		const k2v = [vx + (DT / 2) * k1a[0], vy + (DT / 2) * k1a[1]];
		const k2a = acc(x + (DT / 2) * k1v[0], y + (DT / 2) * k1v[1], k2v[0], k2v[1], th);
		const k3v = [vx + (DT / 2) * k2a[0], vy + (DT / 2) * k2a[1]];
		const k3a = acc(x + (DT / 2) * k2v[0], y + (DT / 2) * k2v[1], k3v[0], k3v[1], th);
		const k4v = [vx + DT * k3a[0], vy + DT * k3a[1]];
		const k4a = acc(x + DT * k3v[0], y + DT * k3v[1], k4v[0], k4v[1], th);
		x += (DT / 6) * (k1v[0] + 2 * k2v[0] + 2 * k3v[0] + k4v[0]);
		y += (DT / 6) * (k1v[1] + 2 * k2v[1] + 2 * k3v[1] + k4v[1]);
		vx += (DT / 6) * (k1a[0] + 2 * k2a[0] + 2 * k3a[0] + k4a[0]);
		vy += (DT / 6) * (k1a[1] + 2 * k2a[1] + 2 * k3a[1] + k4a[1]);
		s.x.push(x);
		s.y.push(y);
		s.vx.push(vx);
		s.vy.push(vy);
		if (Math.hypot(x, y) < 0.2) {
			s.hit = true;
			break;
		}
	}
	return s;
}
const rAt = (s: Sim, i: number) => Math.hypot(s.x[i], s.y[i]);

// 1) free flight: first perihelion (the near miss) and the next aphelion
const base = simulate(null, null, TL + 4.5);
let iPeri = 1;
while (iPeri < base.x.length - 1 && !(rAt(base, iPeri) < rAt(base, iPeri - 1) && rAt(base, iPeri) <= rAt(base, iPeri + 1))) iPeri++;
let iApo = iPeri + 1;
while (iApo < base.x.length - 1 && !(rAt(base, iApo) > rAt(base, iApo - 1) && rAt(base, iApo) >= rAt(base, iApo + 1))) iApo++;
export const TAU_PERI = TL + iPeri * DT;
export const TAU_APO = TL + iApo * DT;
// 2) retro burn at aphelion: cancels ~10 % of the speed (not enough on its own)
const BURN = [TAU_APO, TAU_APO + 0.35, 0.4];
const burned = simulate(BURN, null, TAU_APO + 3);
let iV = Math.round((BURN[1] - TL) / DT);
while (iV < burned.x.length - 1 && rAt(burned, iV) >= 0.62) iV++;
export const TAU_VENUS = TL + iV * DT;
// 3) Venus flyby brakes it: now it falls into the Sun
const BRAKE = [TAU_VENUS - 0.09, TAU_VENUS + 0.21, 2.5];
const full = simulate(BURN, BRAKE, TAU_VENUS + 2);
export const TAU_HIT = TL + (full.x.length - 1) * DT;
export const TAU_L = TL;
export const BURN_W = BURN;
export const BRAKE_W = BRAKE;

export type RS = {x: number; y: number; vx: number; vy: number; r: number};
export const rocketSim = (tau: number): RS => {
	const f = clamp((tau - TL) / DT, 0, full.x.length - 1);
	const i = Math.min(Math.floor(f), full.x.length - 2);
	const u = f - i;
	const x = lerp(full.x[i], full.x[i + 1], u);
	const y = lerp(full.y[i], full.y[i + 1], u);
	return {x, y, vx: lerp(full.vx[i], full.vx[i + 1], u), vy: lerp(full.vy[i], full.vy[i + 1], u), r: Math.hypot(x, y)};
};
export const toWorld = (p: {x: number; y: number}): V => ({x: O.x + RE * p.x, y: O.y + RE * p.y});

// Venus waits just outside the rocket's path at the flyby
const pv = rocketSim(TAU_VENUS);
export const VENUS_POS = toWorld({x: pv.x + (pv.x / pv.r) * 0.21, y: pv.y + (pv.y / pv.r) * 0.21});

// ---------------------------------------------------------------- sim clock
// Monotone cubic through (real time, sim time) anchors: every orbital event lands on its word.
const pchip = (xs: number[], ys: number[]) => {
	const n = xs.length;
	const h: number[] = [];
	const d: number[] = [];
	for (let i = 0; i < n - 1; i++) {
		h.push(xs[i + 1] - xs[i]);
		d.push((ys[i + 1] - ys[i]) / h[i]);
	}
	const m = new Array(n).fill(0);
	m[0] = d[0];
	m[n - 1] = d[n - 2];
	for (let i = 1; i < n - 1; i++) {
		if (d[i - 1] * d[i] <= 0) m[i] = 0;
		else {
			const w1 = 2 * h[i] + h[i - 1];
			const w2 = h[i] + 2 * h[i - 1];
			m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]);
		}
	}
	return (x: number) => {
		if (x <= xs[0]) return ys[0];
		if (x >= xs[n - 1]) return ys[n - 1] + m[n - 1] * (x - xs[n - 1]);
		let i = 0;
		while (x > xs[i + 1]) i++;
		const t = (x - xs[i]) / h[i];
		const t2 = t * t;
		const t3 = t2 * t;
		return (
			(2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1]
		);
	};
};
export const T_HIT = 20.2;
export const tauAt = pchip(
	[0, 7.95, 9.2, 10.5, 12.95, 15.5, 16.35, 19.15, T_HIT, DUR],
	[0, 0, 0.38, TL, TAU_PERI, TAU_APO, BURN[1], TAU_VENUS, TAU_HIT, TAU_HIT + 0.3],
);
export const earthAt = (tau: number): V => ({x: O.x + RE * Math.sin(tau), y: O.y + RE * Math.cos(tau)});
export const feetAt = (tau: number): V => {
	const e = earthAt(tau);
	return {x: e.x, y: e.y - EARTH_R + 22};
};
export const rocketVisible = (t: number) => t >= SW.release && t < T_HIT + 0.02;
export const rocketWorld = (t: number) => toWorld(rocketSim(tauAt(t)));

// ---------------------------------------------------------------- camera
const K0: Cam = {x: 540, y: 960, z: 0};
const K1: Cam = {x: 560, y: 1010, z: 220};
const KW: Cam = {x: 540, y: 107, z: -3762};
const lerpCam = (a: Cam, b: Cam, u: number): Cam => {
	const ka = kOf(a.z);
	const kb = kOf(b.z);
	return {x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), z: zOfK(Math.exp(lerp(Math.log(ka), Math.log(kb), u)))};
};
// smoothed rocket position (centred moving average) for a calm follow camera
const SMOOTH = 24;
const rocketTrack: V[] = [];
for (let f = 0; f <= NF; f++) {
	const t = f / FPS;
	const tt = clamp(t, SW.release, T_HIT);
	rocketTrack.push(rocketWorld(tt));
}
const rocketSmooth: V[] = rocketTrack.map((_, f) => {
	let sx = 0;
	let sy = 0;
	let n = 0;
	for (let j = f - SMOOTH; j <= f + SMOOTH; j++) {
		const p = rocketTrack[clamp(j, 0, NF)];
		sx += p.x;
		sy += p.y;
		n++;
	}
	return {x: sx / n, y: sy / n};
});
const follow = (f: number, m: number, k: number): Cam => {
	const r = rocketSmooth[clamp(f, 0, NF)];
	return {x: lerp(O.x, r.x, m), y: lerp(O.y, r.y, m), z: zOfK(k)};
};
export const headWorld = (feet: V) => {
	const h = SPR.hero;
	const s = HEAD_R / h.head[2];
	return {x: feet.x + (h.head[0] - h.feet[0]) * s, y: feet.y + (h.head[1] - h.feet[1]) * s};
};
const CLOSE_Y = 770; // screen y of the head centre in the reaction close-up
export const closeCam = (t: number): Cam => {
	const k = lerp(2.9, 3.1, clamp((t - SW.closeIn) / (SW.closeOut - SW.closeIn)));
	const head = headWorld(feetAt(tauAt(t)));
	return {x: head.x, y: head.y + (960 - CLOSE_Y) / k, z: zOfK(k)};
};
const endCam = (t: number): Cam => {
	const e = earthAt(tauAt(t));
	return {x: e.x + 20, y: e.y - 850, z: 0};
};
export const isClose = (t: number) => t >= SW.closeIn && t < SW.closeOut;

const launchCam = (): Cam => {
	const e = earthAt(tauAt(SW.release));
	return {x: lerp(O.x, e.x, 0.62), y: lerp(O.y, e.y, 0.62), z: zOfK(0.32)};
};
export const camAt = (f: number): Cam => {
	const t = f / FPS;
	if (t < 6.6) return lerpCam(K0, K1, easeInOutSine((t - 0.2) / 6.4));
	if (t < 8.45) return lerpCam(K1, KW, easeInOutCubic((t - 6.6) / 1.85));
	if (t < 9.75) return KW;
	if (t < 10.55) return lerpCam(KW, launchCam(), easeInOutCubic((t - 9.75) / 0.8));
	if (t < SW.closeIn) return lerpCam(launchCam(), follow(f, 0.55, 0.32), easeInOutSine((t - 10.55) / 1.2));
	if (t < SW.closeOut) return closeCam(t);
	if (t < 14.95) return follow(f, 0.55, 0.32);
	if (t < 16.9) return lerpCam(follow(f, 0.55, 0.32), follow(f, 0.92, 0.8), easeInOutSine((t - 14.95) / 0.75));
	if (t < 20.25) return lerpCam(follow(f, 0.92, 0.8), follow(f, 0.5, 0.3), easeInOutSine((t - 16.9) / 1.5));
	const f0 = Math.round(20.25 * FPS);
	return lerpCam(follow(f0, 0.5, 0.3), endCam(t), easeInOutCubic((t - 20.25) / 0.72));
};

// Sun: its own place in the opening (real parallax), locked onto the orbit centre in the
// space shots, back to its opening place (relative to Earth) at the end so the loop matches.
export const sunWeight = (t: number) =>
	t < 6.6 ? 0 : t < 8.3 ? easeInOutSine((t - 6.6) / 1.7) : t < 20.25 ? 1 : 1 - easeInOutCubic((t - 20.25) / 0.72);
const lockXY = (cam: Cam, target: V, Z: number): V => {
	const r = (Z - cam.z) / (ZP - cam.z);
	return {x: cam.x + (target.x - cam.x) * r, y: cam.y + (target.y - cam.y) * r};
};
export const sunWorld = (t: number, cam: Cam): V => {
	const e = earthAt(tauAt(t));
	const a = {x: S_A.x + e.x - E0.x, y: S_A.y + e.y - E0.y};
	let target: V = O;
	if (isClose(t)) {
		const k = kOf(cam.z);
		target = {x: cam.x + (190 - 540) / k, y: cam.y + (300 - 960) / k};
	}
	return mixV(a, lockXY(cam, target, ZS), sunWeight(t));
};
export const marsWorld = (t: number) => {
	const w = sunWeight(t);
	return {p: mixV(M_A, M_W, w), r: lerp(187, 450, w)};
};

// ---------------------------------------------------------------- shake + depth of field
const bump = (t: number, t0: number, a: number, decay: number) => (t >= t0 ? a * Math.exp(-(t - t0) * decay) : 0);
export const shakeAt = (t: number): V => {
	const amp = bump(t, SW.release, 7, 6) + bump(t, 19.45, 6, 7) + bump(t, T_HIT, 24, 4.2);
	const w = 2 * Math.PI;
	return {
		x: amp * (0.6 * Math.sin(t * w * 13.3) + 0.4 * Math.sin(t * w * 7.1 + 1)),
		y: amp * (0.6 * Math.sin(t * w * 11.7 + 2) + 0.4 * Math.sin(t * w * 5.3)),
	};
};
export const farBlur = (t: number) => {
	if (isClose(t)) return 3.6;
	if (t < 1.2) return 0;
	if (t < 4) return lerp(0, 2.4, easeInOutSine((t - 1.2) / 2.8));
	if (t < 6.6) return 2.4;
	if (t < 7.6) return lerp(2.4, 0, easeInOutSine((t - 6.6) / 1));
	return 0;
};
