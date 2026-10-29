import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {SPR} from './sprites';
import {Brow, Eye, EyeState, Mouth, MouthKind, Puff, Sweat} from './faces';
import {
	Cam,
	EARTH_R,
	FPS,
	HEAD_R,
	O,
	RE,
	ROCKET_SCALE,
	SUN_R,
	SW,
	T,
	T_HIT,
	V,
	VENUS_POS,
	VENUS_R,
	VO_AT,
	WIND_ROCKET_ANGLE,
	ZM,
	ZP,
	ZS,
	ZST,
	camAt,
	clamp,
	earthAt,
	easeInOutCubic,
	easeOutBack,
	easeOutCubic,
	farBlur,
	feetAt,
	headWorld,
	isClose,
	kOf,
	lerp,
	marsWorld,
	popOnOff,
	rocketSim,
	rocketVisible,
	rocketWorld,
	shakeAt,
	spring,
	sunWorld,
	tauAt,
} from './timeline';

type SprName = keyof typeof SPR;
const TAU = Math.PI * 2;

// ------------------------------------------------------------------ 2.5D layer
const Layer: React.FC<{cam: Cam; z: number; blur?: number; minDepth?: number; children: React.ReactNode}> = ({
	cam,
	z,
	blur = 0,
	minDepth = 300,
	children,
}) => {
	const d = z - cam.z;
	if (d < minDepth) return null;
	const k = 1000 / d;
	return (
		<AbsoluteFill style={{filter: blur > 0.05 ? `blur(${blur}px)` : undefined}}>
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					transformOrigin: '0 0',
					transform: `translate(540px, 960px) scale(${k}) translate(${-cam.x}px, ${-cam.y}px)`,
				}}
			>
				{children}
			</div>
		</AbsoluteFill>
	);
};
const project = (p: V, z: number, cam: Cam): V => {
	const k = 1000 / (z - cam.z);
	return {x: 540 + (p.x - cam.x) * k, y: 960 + (p.y - cam.y) * k};
};
const WorldSvg: React.FC<{children: React.ReactNode}> = ({children}) => (
	<svg width={1} height={1} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
		{children}
	</svg>
);

// A cut-out placed in the world: `anchor` (sprite px) lands on `at` (world px)
const Placed: React.FC<{
	name: SprName;
	at: V;
	anchor: readonly [number, number] | number[];
	scale: number;
	rot?: number;
	sx?: number;
	sy?: number;
	children?: React.ReactNode;
}> = ({name, at, anchor, scale, rot = 0, sx = 1, sy = 1, children}) => {
	const sp = SPR[name];
	return (
		<div
			style={{
				position: 'absolute',
				left: at.x - anchor[0] * scale,
				top: at.y - anchor[1] * scale,
				width: sp.w * scale,
				height: sp.h * scale,
				transformOrigin: `${anchor[0] * scale}px ${anchor[1] * scale}px`,
				transform: `rotate(${rot}deg) scale(${sx}, ${sy})`,
			}}
		>
			<Img src={staticFile(`sun/${name}.png`)} style={{width: '100%', height: '100%', display: 'block'}} />
			{children ? (
				<svg
					viewBox={`0 0 ${sp.w} ${sp.h}`}
					style={{position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', overflow: 'visible'}}
				>
					{children}
				</svg>
			) : null}
		</div>
	);
};

// ------------------------------------------------------------------ helpers
const norm = (v: V): V => {
	const l = Math.hypot(v.x, v.y) || 1;
	return {x: v.x / l, y: v.y / l};
};
const blinkAt = (t: number, times: number[]) => times.some((b) => t >= b && t < b + 0.13);
const rng = (seed: number) => () => {
	seed |= 0;
	seed = (seed + 0x6d2b79f5) | 0;
	let r = Math.imul(seed ^ (seed >>> 15), 1 | seed);
	r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
	return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
};
const STARS = (() => {
	const r = rng(7);
	return Array.from({length: 520}, () => ({
		x: lerp(-9000, 10000, r()),
		y: lerp(-16000, 14000, r()),
		s: lerp(14, 46, Math.pow(r(), 2.2)),
		c: ['#FFF3C4', '#FFFFFF', '#D4E6FF'][Math.floor(r() * 3)],
		ph: r() * TAU,
		sp: lerp(0.6, 1.6, r()),
	}));
})();

// ------------------------------------------------------------------ guy poses
type PoseName = 'hero' | 'worried' | 'brace' | 'windup' | 'follow' | 'cheer';
const POSES: {at: number; name: PoseName; mirror: boolean}[] = [
	{at: 0, name: 'hero', mirror: false},
	{at: SW.worried, name: 'worried', mirror: false},
	{at: SW.brace, name: 'brace', mirror: false},
	{at: SW.windup, name: 'windup', mirror: true},
	{at: SW.release, name: 'follow', mirror: true},
	{at: SW.cheer, name: 'cheer', mirror: false},
];
const poseAt = (t: number) => {
	let i = 0;
	while (i + 1 < POSES.length && t >= POSES[i + 1].at) i++;
	const cur = POSES[i];
	const next = POSES[i + 1];
	// anticipation squash before the swap, stretch + damped spring after it
	const antic = next && t >= next.at - 0.1 ? (t - (next.at - 0.1)) / 0.1 : 0;
	const spr = i > 0 ? spring(t, cur.at, 8, 30) : 0;
	let sx = 1 + 0.04 * antic - 0.03 * spr;
	let sy = 1 - 0.06 * antic + 0.05 * spr;
	// the turn (brace -> mirrored wind-up) hides inside a narrow squash
	const turn = Math.max(0, 1 - Math.abs(t - SW.windup) / 0.08);
	sx *= 1 - 0.2 * turn;
	sy *= 1 + 0.03 * turn;
	sy *= 1 + 0.009 * Math.sin(t * TAU * 0.6); // breathing
	let lean = 0;
	if (t >= SW.windup && t < SW.release) lean = 7 * easeOutCubic((t - SW.windup) / 0.3);
	if (t >= SW.release) lean = -7 * Math.exp(-(t - SW.release) * 3.5) * Math.cos((t - SW.release) * 9);
	let dx = 0;
	let dy = 0;
	if (cur.name === 'brace') dx = 2.2 * Math.sin(t * TAU * 12) + 1.6 * Math.sin(t * TAU * 17.3);
	if (cur.name === 'cheer') {
		const u = (t - SW.cheer) / 0.38;
		if (u < 1) dy = -70 * Math.sin(Math.PI * clamp(u));
	}
	return {...cur, sx, sy, lean, dx, dy};
};

const Guy: React.FC<{t: number}> = ({t}) => {
	const feet = feetAt(tauAt(t));
	if (isClose(t)) {
		// waist-up reaction: head goes where the full-body head is
		const sp = SPR.facepalm;
		const s = HEAD_R / sp.head[2];
		const head = headWorld(feet);
		const kick = spring(t, SW.closeIn, 9, 26);
		return <Placed name="facepalm" at={head} anchor={[sp.head[0], sp.head[1]]} scale={s} sx={1 + 0.03 * kick} sy={1 - 0.03 * kick} />;
	}
	const p = poseAt(t);
	const sp = SPR[p.name];
	const s = HEAD_R / sp.head[2];
	const at = {x: feet.x + p.dx, y: feet.y + p.dy};
	// worried sweat drop
	const sweat = popOnOff(t, 3.0, 4.15, 0.14);
	const slide = clamp((t - 3.1) / 1.0);
	return (
		<>
			<WorldSvg>
				<ellipse cx={feet.x} cy={feet.y + 4} rx={150} ry={20} fill="rgba(14, 26, 70, 0.32)" />
			</WorldSvg>
			<Placed name={p.name} at={at} anchor={[sp.feet[0], sp.feet[1]]} scale={s} rot={p.lean} sx={(p.mirror ? -1 : 1) * p.sx} sy={p.sy} />
			{sweat > 0 ? (
				<WorldSvg>
					<Sweat x={headWorld(feet).x + 120} y={headWorld(feet).y - 60 + 60 * slide} size={46} sw={6} scale={sweat} />
				</WorldSvg>
			) : null}
		</>
	);
};

// ------------------------------------------------------------------ Sun
const sunFace = (t: number, look: V): {eye: EyeState; mouth: MouthKind; mouthOpen: number; brow: number; browLift: number} => {
	const blink = blinkAt(t, [4.55, 9.4, 15.0, 17.7]);
	let eye: EyeState = {open: 1, look, pop: 1};
	let mouth: MouthKind = 'smile';
	let mouthOpen = 1;
	let brow = 0;
	let browLift = 0;
	if (t < T.sun) eye = {...eye, closed: 'sleep'};
	else if (t < T.sun + 0.25) eye = {...eye, pop: lerp(0.35, 1, easeOutBack((t - T.sun) / 0.25))};
	if (t >= 3.0 && t < 5.5) {
		eye = {...eye, open: 0.55};
		mouth = 'smirk';
	}
	if (t >= 12.45 && t < 13.2) {
		eye = {...eye, open: 1};
		mouth = 'o';
		mouthOpen = clamp((t - 12.45) / 0.3);
		browLift = 25;
	}
	if (t >= SW.closeOut && t < 19.3) {
		eye = {...eye, open: 0.6};
		mouth = 'smirk';
		brow = 6;
	}
	if (t >= 19.3 && t < T_HIT) {
		eye = {...eye, open: 1, pop: 1 + 0.12 * easeOutBack((t - 19.3) / 0.25)};
		mouth = 'o';
		mouthOpen = lerp(0.5, 1.2, clamp((t - 19.3) / 0.8));
		brow = -16;
		browLift = 30;
	}
	if (t >= T_HIT && t < T_HIT + 0.55) {
		eye = {...eye, closed: 'squeeze'};
		mouth = 'wavy';
		brow = -10;
	}
	if (t >= T_HIT + 0.55) {
		eye = {...eye, closed: 'happy'};
		mouth = 'smile';
	}
	if (blink && !eye.closed) eye = {...eye, open: 0.03};
	return {eye, mouth, mouthOpen, brow, browLift};
};

const Sun: React.FC<{t: number; cam: Cam}> = ({t, cam}) => {
	const sp = SPR.sun;
	const scale = SUN_R / sp.r;
	const pos = sunWorld(t, cam);
	const scr = project(pos, ZS, cam);
	// what the Sun watches (screen-space direction)
	let target: V;
	if (t < 5.6) target = project(headWorld(feetAt(0)), ZP, cam);
	else if (t < 6.4) target = project(marsWorld(t).p, ZM, cam);
	else if (rocketVisible(t)) target = project(rocketWorld(t), ZP, cam);
	else target = project(earthAt(tauAt(t)), ZP, cam);
	const look = norm({x: target.x - scr.x, y: target.y - scr.y});
	const f = sunFace(t, look);
	const squash = spring(t, T_HIT, 7, 22);
	const [dcx, dcy] = [sp.disc[0], sp.disc[1]];
	const sweat = popOnOff(t, 19.6, 20.85, 0.14);
	return (
		<Placed name="sun" at={pos} anchor={[dcx, dcy]} scale={scale} sx={1 + 0.07 * squash} sy={1 - 0.1 * squash}>
			<Brow cx={dcx - 210} cy={1010} len={150} sw={26} tilt={f.brow} side={-1} lift={f.browLift} />
			<Brow cx={dcx + 210} cy={1010} len={150} sw={26} tilt={f.brow} side={1} lift={f.browLift} />
			<Eye id="sunL" cx={dcx - 210} cy={1165} rx={86} ry={104} sw={26} side={-1} s={f.eye} />
			<Eye id="sunR" cx={dcx + 210} cy={1165} rx={86} ry={104} sw={26} side={1} s={f.eye} />
			<Mouth cx={dcx} cy={1385} w={230} sw={26} kind={f.mouth} open={f.mouthOpen} />
			<Sweat x={dcx + 470} y={900 + 120 * clamp((t - 19.7) / 1)} size={110} sw={22} scale={sweat} />
		</Placed>
	);
};

// ------------------------------------------------------------------ Earth
const Earth: React.FC<{t: number; cam: Cam}> = ({t, cam}) => {
	const sp = SPR.earth;
	const scale = EARTH_R / sp.r;
	const tau = tauAt(t);
	const e = earthAt(tau);
	let eye: EyeState = {open: 1, look: {x: 0, y: -0.3}};
	let mouth: MouthKind = 'smile';
	let browLift = 0;
	if (t < T.earth) eye = {...eye, closed: 'sleep'};
	else if (t < T.earth + 0.25) eye = {...eye, pop: lerp(0.35, 1, easeOutBack((t - T.earth) / 0.25))};
	if (t >= 7.9 && t < 10.4) {
		eye = {...eye, look: {x: Math.cos(tau), y: -Math.sin(tau)}};
		mouth = 'grin';
		browLift = 40;
	}
	if (t >= 10.4 && rocketVisible(t)) {
		const r = project(rocketWorld(t), ZP, cam);
		const me = project(e, ZP, cam);
		eye = {...eye, look: norm({x: r.x - me.x, y: r.y - me.y})};
	}
	if (t >= T_HIT) {
		eye = {...eye, closed: 'happy'};
		mouth = 'grin';
	}
	if (blinkAt(t, [11.7, 16.2]) && !eye.closed) eye = {...eye, open: 0.03};
	return (
		<Placed name="earth" at={e} anchor={[sp.c[0], sp.c[1]]} scale={scale}>
			<Brow cx={600} cy={630} len={150} sw={24} tilt={-6} side={-1} lift={browLift} />
			<Brow cx={1040} cy={630} len={150} sw={24} tilt={-6} side={1} lift={browLift} />
			<Eye id="eaL" cx={600} cy={775} rx={92} ry={110} sw={24} side={-1} s={eye} />
			<Eye id="eaR" cx={1040} cy={775} rx={92} ry={110} sw={24} side={1} s={eye} />
			<Mouth cx={820} cy={1010} w={260} sw={24} kind={mouth} />
		</Placed>
	);
};

// ------------------------------------------------------------------ Mars + Venus
const Mars: React.FC<{t: number}> = ({t}) => {
	const pop = popOnOff(t, T.mars, 20.3, 0.22);
	if (pop <= 0.01 || isClose(t)) return null;
	const sp = SPR.mars;
	const {p, r} = marsWorld(t);
	const wink = t >= 5.95 && t < 6.3;
	const eyeL: EyeState = {open: 0.55, look: {x: 0.7, y: 0.4}};
	const eyeR: EyeState = wink ? {open: 0, look: {x: 0, y: 0}, closed: 'happy'} : eyeL;
	return (
		<Placed name="mars" at={p} anchor={[sp.c[0], sp.c[1]]} scale={(r / sp.r) * pop}>
			<Brow cx={322} cy={300} len={110} sw={22} tilt={4} side={-1} />
			<Brow cx={562} cy={300} len={110} sw={22} tilt={-8} side={1} lift={wink ? 18 : 0} />
			<Eye id="maL" cx={322} cy={405} rx={62} ry={74} sw={22} side={-1} s={eyeL} />
			<Eye id="maR" cx={562} cy={405} rx={62} ry={74} sw={22} side={1} s={eyeR} />
			<Mouth cx={442} cy={570} w={170} sw={22} kind="smirk" />
		</Placed>
	);
};

const Venus: React.FC<{t: number; cam: Cam}> = ({t, cam}) => {
	const pop = popOnOff(t, 18.55, 99, 0.22);
	if (pop <= 0.01) return null;
	const sp = SPR.venus;
	const me = project(VENUS_POS, ZP, cam);
	const r = rocketVisible(t) ? project(rocketWorld(t), ZP, cam) : project(O, ZP, cam);
	const look = norm({x: r.x - me.x, y: r.y - me.y});
	const grab = t >= 19.1 && t < 19.65;
	let eye: EyeState = {open: 1, look};
	let mouth: MouthKind = 'smile';
	let brow = 0;
	if (grab) {
		eye = {...eye, lidTilt: 20, open: 0.85};
		mouth = 'flat';
		brow = 22;
	}
	if (t >= 19.65) {
		eye = {...eye, open: 0.55};
		mouth = 'smirk';
	}
	// inhale toward the rocket, then squash as it brakes it
	const inhale = t >= 19.1 && t < 19.4 ? Math.sin(((t - 19.1) / 0.3) * Math.PI) : 0;
	const kick = spring(t, 19.4, 8, 24);
	return (
		<Placed
			name="venus"
			at={VENUS_POS}
			anchor={[sp.c[0], sp.c[1]]}
			scale={(VENUS_R / sp.r) * pop}
			sx={1 - 0.05 * inhale + 0.06 * kick}
			sy={1 + 0.07 * inhale - 0.08 * kick}
		>
			<Brow cx={390} cy={385} len={120} sw={24} tilt={brow} side={-1} />
			<Brow cx={670} cy={385} len={120} sw={24} tilt={brow} side={1} />
			<Eye id="veL" cx={390} cy={500} rx={74} ry={88} sw={24} side={-1} s={eye} />
			<Eye id="veR" cx={670} cy={500} rx={74} ry={88} sw={24} side={1} s={eye} />
			<Mouth cx={530} cy={690} w={190} sw={24} kind={mouth} />
		</Placed>
	);
};

// ------------------------------------------------------------------ rocket
const angDeg = (vx: number, vy: number) => (Math.atan2(vx, -vy) * 180) / Math.PI;
const shortest = (a: number, b: number) => {
	let d = ((b - a) % 360 + 540) % 360 - 180;
	return a + d;
};
const rocketPose = (t: number) => {
	const tau = tauAt(t);
	const s = rocketSim(tau);
	let rot = angDeg(s.vx, s.vy);
	const u = clamp((t - SW.release) / 0.18);
	rot = shortest(rot, lerp(shortest(rot, WIND_ROCKET_ANGLE), rot, easeOutCubic(u)));
	// flip around for the retro burn, flip back after the sputter
	const flip = t < 15.3 ? 0 : t < 15.5 ? easeInOutCubic((t - 15.3) / 0.2) : t < 16.85 ? 1 : 1 - easeInOutCubic((t - 16.85) / 0.3);
	rot += 180 * flip;
	const pos = rocketWorld(t);
	let scale = ROCKET_SCALE;
	if (s.r < 0.27) scale *= clamp((s.r - 0.2) / 0.07, 0.25, 1); // sinking into the Sun
	const speed = Math.hypot(s.vx, s.vy);
	return {pos, rot, scale, speed, s};
};
const NOZZLE: V = {x: 276, y: 990};
const nozzleWorld = (t: number) => {
	const p = rocketPose(t);
	const a = (p.rot * Math.PI) / 180;
	const lx = (NOZZLE.x - SPR.rocket.redC[0]) * p.scale;
	const ly = (NOZZLE.y - SPR.rocket.redC[1]) * p.scale;
	return {x: p.pos.x + lx * Math.cos(a) - ly * Math.sin(a), y: p.pos.y + lx * Math.sin(a) + ly * Math.cos(a)};
};
const flameLen = (t: number) => {
	const flick = 1 + 0.12 * Math.sin(t * TAU * 17) + 0.08 * Math.sin(t * TAU * 29 + 1);
	if (t >= SW.release && t < 11.35) return 430 * (t < 10.9 ? 1 : 1 - easeInOutCubic((t - 10.9) / 0.45)) * flick;
	if (t >= 15.5 && t < 16.35) return 390 * easeOutBack((t - 15.5) / 0.15) * flick;
	if ((t >= 16.42 && t < 16.5) || (t >= 16.6 && t < 16.65)) return 160 * flick;
	return 0;
};
const Flame: React.FC<{len: number}> = ({len}) => {
	if (len < 4) return null;
	const layer = (k: number, w: number, c: string) => (
		<path
			d={`M ${NOZZLE.x - w} ${NOZZLE.y - 10} C ${NOZZLE.x - w} ${NOZZLE.y + len * k * 0.45} ${NOZZLE.x - w * 0.25} ${NOZZLE.y + len * k * 0.8} ${NOZZLE.x} ${NOZZLE.y + len * k} C ${NOZZLE.x + w * 0.25} ${NOZZLE.y + len * k * 0.8} ${NOZZLE.x + w} ${NOZZLE.y + len * k * 0.45} ${NOZZLE.x + w} ${NOZZLE.y - 10} Z`}
			fill={c}
		/>
	);
	return (
		<g>
			{layer(1, 78, '#FF6A2B')}
			{layer(0.72, 56, '#FFA445')}
			{layer(0.42, 34, '#FFC867')}
		</g>
	);
};
const rocketEye = (t: number, rotDeg: number, cam: Cam): EyeState => {
	const toLocal = (w: V) => {
		const a = (-rotDeg * Math.PI) / 180;
		return norm({x: w.x * Math.cos(a) - w.y * Math.sin(a), y: w.x * Math.sin(a) + w.y * Math.cos(a)});
	};
	const me = rocketWorld(t);
	const sunDir = toLocal(norm({x: O.x - me.x, y: O.y - me.y}));
	const venusDir = toLocal(norm({x: VENUS_POS.x - me.x, y: VENUS_POS.y - me.y}));
	if (t < 11.0) return {open: 0, look: {x: 0, y: 0}, closed: 'happy'};
	if (t < 12.4) return {open: 1, look: {x: 0, y: -1}};
	if (t < 13.4) return {open: 1, look: sunDir, pop: 1.08};
	if (t < 15.35) return {open: 0.6, look: sunDir};
	if (t < 16.4) return {open: 0, look: {x: 0, y: 0}, closed: 'squeeze'};
	if (t < 17.3) return {open: 0.55, look: {x: 0, y: 0.5}};
	if (t < 19.15) return {open: 1, look: venusDir};
	if (t < 19.6) return {open: 0, look: {x: 0, y: 0}, closed: 'squeeze'};
	return {open: 1, look: sunDir, pop: 1.15};
};
const Rocket: React.FC<{t: number; cam: Cam}> = ({t, cam}) => {
	if (!rocketVisible(t)) return null;
	const p = rocketPose(t);
	const sp = SPR.rocket;
	const brake = spring(t, 19.4, 7, 26);
	const sweat = popOnOff(t, 16.35, 17.2, 0.14);
	const lines = clamp((p.speed - 1.08) * 700, 0, 520);
	return (
		<Placed
			name="rocket"
			at={p.pos}
			anchor={[sp.redC[0], sp.redC[1]]}
			scale={p.scale}
			rot={p.rot}
			sx={1 + 0.1 * brake}
			sy={1 - 0.14 * brake}
		>
			{lines > 10 && flameLen(t) < 4 ? (
				<g>
					{[-80, 0, 80].map((dx, i) => (
						<g key={i}>
							<line x1={276 + dx} y1={1070 + i * 40} x2={276 + dx} y2={1070 + i * 40 + lines * (1 - i * 0.18)} stroke="#111" strokeWidth={44} strokeLinecap="round" />
							<line x1={276 + dx} y1={1070 + i * 40} x2={276 + dx} y2={1070 + i * 40 + lines * (1 - i * 0.18)} stroke="#fff" strokeWidth={24} strokeLinecap="round" />
						</g>
					))}
				</g>
			) : null}
			<Flame len={flameLen(t)} />
			<Eye id="rk" cx={278} cy={397} rx={58} ry={58} sw={16} side={-1} s={rocketEye(t, p.rot, cam)} />
			<Sweat x={455} y={300 + 90 * clamp((t - 16.45) / 0.7)} size={70} sw={16} scale={sweat} />
		</Placed>
	);
};

// ------------------------------------------------------------------ plane effects
const OrbitPath: React.FC<{t: number}> = ({t}) => {
	const vis = clamp((t - 8.2) / 0.5) * (1 - clamp((t - 20.3) / 0.4));
	if (vis <= 0 || isClose(t)) return null;
	return (
		<circle cx={O.x} cy={O.y} r={RE} fill="none" stroke={`rgba(255,255,255,${0.24 * vis})`} strokeWidth={20} strokeDasharray="80 90" strokeLinecap="round" />
	);
};
const WindLines: React.FC<{t: number}> = ({t}) => {
	const amt = t < 7.95 ? 0 : t < 8.25 ? easeOutCubic((t - 7.95) / 0.3) : t < 10.1 ? 1 : 1 - easeInOutCubic((t - 10.1) / 0.35);
	if (amt <= 0) return null;
	const tau = tauAt(t);
	const e = earthAt(tau);
	const u = {x: Math.cos(tau), y: -Math.sin(tau)}; // direction of motion
	// anchor points around the Earth and the guy standing on it (world offsets from Earth centre)
	const pts = [
		{x: -300, y: 170},
		{x: 260, y: -90},
		{x: 330, y: 230},
		{x: -230, y: -260},
		{x: -150, y: -620},
		{x: 200, y: -830},
		{x: -60, y: -1060},
	];
	return (
		<g>
			{pts.map((o, i) => {
				const cyc = (t * 2.2 + i * 0.37) % 1;
				const along = 120 + cyc * 520;
				const len = (240 + 120 * Math.sin(i * 2.1)) * amt * Math.sin(Math.PI * cyc);
				const sx = e.x + o.x - u.x * along;
				const sy = e.y + o.y - u.y * along;
				const ex = sx - u.x * len;
				const ey = sy - u.y * len;
				if (len < 6) return null;
				return (
					<g key={i}>
						<line x1={sx} y1={sy} x2={ex} y2={ey} stroke="#111" strokeWidth={42} strokeLinecap="round" />
						<line x1={sx} y1={sy} x2={ex} y2={ey} stroke="#fff" strokeWidth={26} strokeLinecap="round" />
					</g>
				);
			})}
		</g>
	);
};
const Trail: React.FC<{t: number}> = ({t}) => {
	if (!rocketVisible(t)) return null;
	const dots = [];
	for (let i = 2; i <= 26; i++) {
		const tt = t - i * 0.05;
		if (tt < SW.release + 0.05) break;
		const p = rocketWorld(tt);
		dots.push(<circle key={i} cx={p.x} cy={p.y} r={18 * (1 - i / 28)} fill="rgba(255, 236, 170, 0.75)" />);
	}
	return <g>{dots}</g>;
};
const puffCircles = (c: V, size: number, seed: number) => {
	const r = rng(seed);
	return Array.from({length: 4}, (_, i) => {
		const a = (i / 4) * TAU + r() * 0.8;
		const d = size * (i === 0 ? 0 : 0.55);
		return {x: c.x + Math.cos(a) * d, y: c.y + Math.sin(a) * d, r: size * lerp(0.55, 0.8, r())};
	});
};
// grow, drift, then SHRINK away (outlined puffs never fade)
const PuffAt: React.FC<{t: number; t0: number; at: V; drift: V; size: number; fill: string; seed: number; life?: number}> = ({
	t,
	t0,
	at,
	drift,
	size,
	fill,
	seed,
	life = 0.9,
}) => {
	const u = (t - t0) / life;
	if (u < 0 || u > 1) return null;
	const grow = u < 0.25 ? easeOutBack(u / 0.25, 1.4) : 1 - easeInOutCubic((u - 0.25) / 0.75);
	const c = {x: at.x + drift.x * u, y: at.y + drift.y * u};
	return <Puff circles={puffCircles(c, size * grow + 0.01, seed)} sw={8} fill={fill} />;
};
const Puffs: React.FC<{t: number}> = ({t}) => {
	const out: React.ReactNode[] = [];
	// launch steam at the hand
	if (t >= SW.release && t < SW.release + 1.2) {
		const n0 = nozzleWorld(SW.release + 0.02);
		[0, 0.06, 0.12].forEach((d, i) =>
			out.push(
				<PuffAt key={`l${i}`} t={t} t0={SW.release + d} at={{x: n0.x + (i - 1) * 60, y: n0.y + 30}} drift={{x: (i - 1) * 140, y: 120}} size={70} fill="#F4F6FA" seed={11 + i} />,
			),
		);
	}
	// sputtering engine: grey smoke
	[16.36, 16.5, 16.64, 16.78].forEach((t0, i) => {
		if (t >= t0 && t < t0 + 1) {
			const at = nozzleWorld(t0);
			out.push(<PuffAt key={`s${i}`} t={t} t0={t0} at={at} drift={{x: 30 * (i % 2 ? 1 : -1), y: -90}} size={58 + i * 6} fill="#8A90A0" seed={31 + i} />);
		}
	});
	// Venus brake: two little puffs at the nose
	[19.38, 19.46].forEach((t0, i) => {
		if (t >= t0 && t < t0 + 0.8) {
			const p = rocketWorld(t0);
			out.push(<PuffAt key={`b${i}`} t={t} t0={t0} at={{x: p.x + (i ? 50 : -50), y: p.y - 40}} drift={{x: (i ? 1 : -1) * 90, y: -60}} size={48} fill="#F4F6FA" seed={51 + i} life={0.7} />);
		}
	});
	return <g>{out}</g>;
};
const HIT_AT = rocketWorld(T_HIT - 0.02);
const Impact: React.FC<{t: number}> = ({t}) => {
	if (t < T_HIT) return null;
	const u = t - T_HIT;
	const out = norm({x: HIT_AT.x - O.x, y: HIT_AT.y - O.y});
	const ring = clamp(u / 0.4);
	const r = rng(99);
	const blobs = Array.from({length: 9}, (_, i) => {
		const a = Math.atan2(out.y, out.x) + (i / 8 - 0.5) * 2.2 + (r() - 0.5) * 0.3;
		const v = lerp(700, 1300, r());
		const tt = clamp(u, 0, 0.75);
		const vx = Math.cos(a) * v;
		const vy = Math.sin(a) * v;
		// gravity pulls the splash back toward the Sun
		const g = 2600;
		const x = HIT_AT.x + vx * tt - out.x * 0.5 * g * tt * tt;
		const y = HIT_AT.y + vy * tt - out.y * 0.5 * g * tt * tt;
		const size = lerp(40, 22, i % 3 === 0 ? 0 : 1) * (1 - clamp((u - 0.2) / 0.55));
		const vxt = vx - out.x * g * tt;
		const vyt = vy - out.y * g * tt;
		const ang = (Math.atan2(vyt, vxt) * 180) / Math.PI;
		return size > 0.5 ? (
			<g key={i} transform={`translate(${x} ${y}) rotate(${ang})`}>
				<ellipse rx={size * 1.7} ry={size} fill="#E2501E" />
				<ellipse rx={size * 1.3} ry={size * 0.7} fill="#FF6A2B" />
				<ellipse rx={size * 0.7} ry={size * 0.38} fill="#FFC867" />
			</g>
		) : null;
	});
	return (
		<g>
			{ring < 1 ? <circle cx={HIT_AT.x} cy={HIT_AT.y} r={40 + 300 * easeOutCubic(ring)} fill="none" stroke="#FFC867" strokeWidth={46 * (1 - ring)} /> : null}
			{blobs}
			{[0, 0.08, 0.16].map((d, i) => (
				<PuffAt key={i} t={t} t0={T_HIT + 0.05 + d} at={{x: HIT_AT.x + out.x * 60 + (i - 1) * 80, y: HIT_AT.y + out.y * 60}} drift={{x: out.x * 160 + (i - 1) * 60, y: out.y * 160 - 120}} size={64} fill="#FFFFFF" seed={71 + i} life={0.75} />
			))}
		</g>
	);
};

// ------------------------------------------------------------------ sound
type Cue = {f: string; at: number; db: number; keys?: [number, number][]; len?: number};
const CUES: Cue[] = [
	{f: 'pop', at: T.sun - 0.12, db: -27},
	{f: 'pop', at: T.mars - 0.12, db: -24},
	{f: 'whoosh', at: 6.62, db: -28},
	{f: 'wind', at: 7.9, db: -27, len: 2.7, keys: [[0, -60], [0.35, 0], [2.0, 0], [2.7, -60]]},
	{f: 'launch', at: SW.release - 0.05, db: -17},
	{f: 'whoosh', at: 12.95 - 0.2, db: -19},
	{f: 'pop', at: SW.closeIn - 0.02, db: -22},
	{f: 'thruster', at: 15.48, db: -22, len: 1.45, keys: [[0, 0], [1.2, 0], [1.45, -60]]},
	{f: 'pop', at: 18.45, db: -24},
	{f: 'screech', at: 19.42 - 0.66, db: -25},
	{f: 'boom', at: T_HIT - 0.2, db: -13},
	{f: 'sizzle', at: T_HIT - 0.08, db: -19, len: 0.8, keys: [[0, 0], [0.55, 0], [0.8, -60]]},
	{f: 'whoosh', at: 20.24, db: -27},
];
const dbAt = (c: Cue, s: number) => {
	if (!c.keys) return c.db;
	const k = c.keys;
	if (s <= k[0][0]) return c.db + k[0][1];
	for (let i = 0; i < k.length - 1; i++)
		if (s <= k[i + 1][0]) return c.db + lerp(k[i][1], k[i + 1][1], (s - k[i][0]) / (k[i + 1][0] - k[i][0]));
	return c.db + k[k.length - 1][1];
};

// ------------------------------------------------------------------ the short
export const SunShort: React.FC = () => {
	const frame = useCurrentFrame();
	const t = frame / FPS;
	const cam0 = camAt(frame);
	const sh = shakeAt(t);
	const cam = cam0;
	const blur = farBlur(t);
	const sunPos = sunWorld(t, cam);
	const sunScr = project(sunPos, ZS, cam);
	const sunScrR = SUN_R * kOf(cam.z, ZS);
	return (
		<AbsoluteFill style={{background: 'linear-gradient(180deg, #0E1A44 0%, #1A2A62 55%, #283A7A 100%)', overflow: 'hidden'}}>
			<AbsoluteFill style={{transform: `translate(${sh.x}px, ${sh.y}px)`}}>
				{/* warm glow around the Sun */}
				<AbsoluteFill
					style={{
						background: `radial-gradient(circle at ${sunScr.x}px ${sunScr.y}px, rgba(255, 196, 90, 0.26) 0px, rgba(255, 170, 70, 0.10) ${sunScrR * 1.3}px, rgba(255, 170, 70, 0) ${sunScrR * 2.6}px)`,
					}}
				/>
				<Layer cam={cam} z={ZST} blur={blur * 0.6}>
					<WorldSvg>
						{STARS.map((s, i) => {
							const tw = 0.75 + 0.25 * Math.sin(t * s.sp * TAU * 0.5 + s.ph);
							const r = s.s * tw;
							return s.s > 30 ? (
								<path
									key={i}
									d={`M ${s.x} ${s.y - r} Q ${s.x} ${s.y} ${s.x + r} ${s.y} Q ${s.x} ${s.y} ${s.x} ${s.y + r} Q ${s.x} ${s.y} ${s.x - r} ${s.y} Q ${s.x} ${s.y} ${s.x} ${s.y - r} Z`}
									fill={s.c}
								/>
							) : (
								<circle key={i} cx={s.x} cy={s.y} r={r * 0.45} fill={s.c} />
							);
						})}
					</WorldSvg>
				</Layer>
				<Layer cam={cam} z={ZS} blur={blur}>
					<Sun t={t} cam={cam} />
				</Layer>
				<Layer cam={cam} z={ZM} blur={blur}>
					<Mars t={t} />
				</Layer>
				<Layer cam={cam} z={ZP}>
					<WorldSvg>
						<OrbitPath t={t} />
						<WindLines t={t} />
					</WorldSvg>
					{isClose(t) ? null : <Venus t={t} cam={cam} />}
					<WorldSvg>
						<Trail t={t} />
					</WorldSvg>
					<Earth t={t} cam={cam} />
					<Guy t={t} />
					{isClose(t) ? null : <Rocket t={t} cam={cam} />}
					<WorldSvg>
						<Puffs t={t} />
						<Impact t={t} />
					</WorldSvg>
				</Layer>
			</AbsoluteFill>
			<Sequence from={Math.round(VO_AT * FPS)} layout="none">
				<Audio src={staticFile('sun/vo/take1.mp3')} />
			</Sequence>
			{CUES.map((c, i) => (
				<Sequence key={i} from={Math.round(c.at * FPS)} durationInFrames={c.len ? Math.round(c.len * FPS) : undefined} layout="none">
					<Audio src={staticFile(`sun/sfx/${c.f}.wav`)} volume={(f) => Math.pow(10, dbAt(c, f / FPS) / 20)} />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};

