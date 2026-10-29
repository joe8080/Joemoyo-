// Cartoon faces, sweat drops and puffs drawn as SVG in the same flat outlined style as the cut-outs.
import React from 'react';

export type EyeState = {
	open: number; // 1 = fully open, 0.5 = half lids, 0 = closed
	look: {x: number; y: number}; // pupil direction, -1..1
	lidTilt?: number; // deg; positive tilts the lid down toward the nose (angry)
	closed?: 'sleep' | 'happy' | 'squeeze' | null;
	pop?: number; // scale of the whole eye (pop-open overshoot)
};

export const Eye: React.FC<{
	id: string;
	cx: number;
	cy: number;
	rx: number;
	ry: number;
	sw: number;
	side: -1 | 1; // -1 = viewer's left eye
	s: EyeState;
}> = ({id, cx, cy, rx, ry, sw, side, s}) => {
	const pop = s.pop ?? 1;
	const g = `translate(${cx} ${cy}) scale(${pop}) translate(${-cx} ${-cy})`;
	if (s.closed === 'squeeze') {
		// "> <" chevrons pointing at the nose
		const d = side * rx * 0.75;
		return (
			<path
				transform={g}
				d={`M ${cx - d} ${cy - ry * 0.55} L ${cx + d} ${cy} L ${cx - d} ${cy + ry * 0.55}`}
				fill="none"
				stroke="#111"
				strokeWidth={sw * 1.15}
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
		);
	}
	if (s.closed === 'sleep' || s.closed === 'happy' || s.open <= 0.04) {
		const up = s.closed === 'happy' ? -1 : 1;
		return (
			<path
				transform={g}
				d={`M ${cx - rx * 0.85} ${cy} Q ${cx} ${cy + up * ry * 0.7} ${cx + rx * 0.85} ${cy}`}
				fill="none"
				stroke="#111"
				strokeWidth={sw * 1.15}
				strokeLinecap="round"
			/>
		);
	}
	const open = Math.min(1, s.open);
	const pr = Math.min(rx, ry) * 0.46;
	const px = cx + s.look.x * rx * 0.42;
	const py = cy + s.look.y * ry * 0.42;
	const lidY = cy - ry + 2 * ry * (1 - open); // lid bottom edge
	const tilt = (s.lidTilt ?? 0) * -side;
	const clip = `eyeclip-${id}`;
	return (
		<g transform={g}>
			<defs>
				<clipPath id={clip}>
					<ellipse cx={cx} cy={cy} rx={rx} ry={ry} />
				</clipPath>
			</defs>
			<ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="#fff" />
			<g clipPath={`url(#${clip})`}>
				<circle cx={px} cy={py} r={pr} fill="#111" />
				<circle cx={px - pr * 0.32} cy={py - pr * 0.36} r={pr * 0.32} fill="#fff" />
				{open < 0.98 || tilt !== 0 ? (
					<g transform={`rotate(${tilt} ${cx} ${cy})`}>
						<rect x={cx - rx * 2} y={cy - ry * 3} width={rx * 4} height={lidY - (cy - ry * 3)} fill="#C9CCD6" />
						<line x1={cx - rx * 2} y1={lidY} x2={cx + rx * 2} y2={lidY} stroke="#111" strokeWidth={sw * 0.9} />
					</g>
				) : null}
			</g>
			<ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke="#111" strokeWidth={sw} />
		</g>
	);
};

export const Brow: React.FC<{cx: number; cy: number; len: number; sw: number; tilt: number; side: -1 | 1; lift?: number}> = ({
	cx,
	cy,
	len,
	sw,
	tilt,
	side,
	lift = 0,
}) => {
	// tilt > 0: inner end down (angry); tilt < 0: inner end up (worried)
	const a = (tilt * Math.PI) / 180;
	const dx = (len / 2) * Math.cos(a);
	const dy = (len / 2) * Math.sin(a);
	const inner = {x: cx - side * dx, y: cy - lift + dy};
	const outer = {x: cx + side * dx, y: cy - lift - dy};
	const mid = {x: (inner.x + outer.x) / 2, y: (inner.y + outer.y) / 2 - len * 0.12};
	return (
		<path
			d={`M ${inner.x} ${inner.y} Q ${mid.x} ${mid.y} ${outer.x} ${outer.y}`}
			fill="none"
			stroke="#111"
			strokeWidth={sw * 1.5}
			strokeLinecap="round"
		/>
	);
};

export type MouthKind = 'smile' | 'grin' | 'smirk' | 'o' | 'wavy' | 'flat';
export const Mouth: React.FC<{cx: number; cy: number; w: number; sw: number; kind: MouthKind; open?: number}> = ({
	cx,
	cy,
	w,
	sw,
	kind,
	open = 1,
}) => {
	const h = w / 2;
	if (kind === 'smile')
		return (
			<path d={`M ${cx - h} ${cy} Q ${cx} ${cy + w * 0.42} ${cx + h} ${cy}`} fill="none" stroke="#111" strokeWidth={sw} strokeLinecap="round" />
		);
	if (kind === 'smirk')
		return (
			<path
				d={`M ${cx - h * 0.8} ${cy + w * 0.06} Q ${cx + h * 0.1} ${cy + w * 0.2} ${cx + h} ${cy - w * 0.12}`}
				fill="none"
				stroke="#111"
				strokeWidth={sw}
				strokeLinecap="round"
			/>
		);
	if (kind === 'flat')
		return <path d={`M ${cx - h * 0.7} ${cy} L ${cx + h * 0.7} ${cy}`} fill="none" stroke="#111" strokeWidth={sw} strokeLinecap="round" />;
	if (kind === 'wavy') {
		const n = 4;
		let d = `M ${cx - h} ${cy}`;
		for (let i = 0; i < n; i++) {
			const x0 = cx - h + ((i + 0.5) * w) / n;
			const x1 = cx - h + ((i + 1) * w) / n;
			d += ` Q ${x0} ${cy + (i % 2 ? 1 : -1) * w * 0.09} ${x1} ${cy}`;
		}
		return <path d={d} fill="none" stroke="#111" strokeWidth={sw} strokeLinecap="round" />;
	}
	if (kind === 'o') {
		const r = w * 0.3 * open;
		return (
			<g>
				<ellipse cx={cx} cy={cy} rx={r * 0.85} ry={r} fill="#3A1A1A" stroke="#111" strokeWidth={sw} />
				<ellipse cx={cx} cy={cy + r * 0.45} rx={r * 0.5} ry={r * 0.32} fill="#F27D9A" />
			</g>
		);
	}
	// grin: open D shape with tongue
	const dd = w * 0.5 * open;
	const clip = `grin-${Math.round(cx)}-${Math.round(cy)}`;
	return (
		<g>
			<defs>
				<clipPath id={clip}>
					<path d={`M ${cx - h} ${cy} Q ${cx} ${cy + dd * 1.6} ${cx + h} ${cy} Z`} />
				</clipPath>
			</defs>
			<path d={`M ${cx - h} ${cy} Q ${cx} ${cy + dd * 1.6} ${cx + h} ${cy} Z`} fill="#3A1A1A" />
			<g clipPath={`url(#${clip})`}>
				<ellipse cx={cx} cy={cy + dd * 0.85} rx={h * 0.55} ry={dd * 0.45} fill="#F27D9A" />
			</g>
			<path
				d={`M ${cx - h} ${cy} Q ${cx} ${cy + dd * 1.6} ${cx + h} ${cy} Z`}
				fill="none"
				stroke="#111"
				strokeWidth={sw}
				strokeLinejoin="round"
			/>
		</g>
	);
};

// light-blue teardrop with outline + glint; (x, y) = drop centre
export const Sweat: React.FC<{x: number; y: number; size: number; sw: number; scale: number}> = ({x, y, size, sw, scale}) => {
	if (scale <= 0.01) return null;
	const r = size / 2;
	return (
		<g transform={`translate(${x} ${y}) scale(${scale})`}>
			<path
				d={`M 0 ${-r * 1.9} C ${r * 0.35} ${-r * 1.1} ${r} ${-r * 0.5} ${r} ${r * 0.15} A ${r} ${r} 0 1 1 ${-r} ${r * 0.15} C ${-r} ${-r * 0.5} ${-r * 0.35} ${-r * 1.1} 0 ${-r * 1.9} Z`}
				fill="#8FD3FF"
				stroke="#111"
				strokeWidth={sw}
				strokeLinejoin="round"
			/>
			<ellipse cx={-r * 0.38} cy={r * 0.05} rx={r * 0.2} ry={r * 0.32} fill="#fff" />
		</g>
	);
};

// smoke / steam puff cluster with ONE merged outline: all ink circles first, then all fills
export const Puff: React.FC<{circles: {x: number; y: number; r: number}[]; sw: number; fill: string}> = ({circles, sw, fill}) => (
	<g>
		{circles.map((c, i) => (
			<circle key={`i${i}`} cx={c.x} cy={c.y} r={c.r + sw} fill="#111" />
		))}
		{circles.map((c, i) => (
			<circle key={`f${i}`} cx={c.x} cy={c.y} r={c.r} fill={fill} />
		))}
	</g>
);
