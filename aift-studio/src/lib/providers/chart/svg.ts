import type { ChartRenderer, ChartSpec } from '@/lib/providers/types';

/**
 * Deterministic chart renderer.
 *
 * Charts in this product are drawn from validated data rows by code. They are
 * never produced by an image model, and `visibleValues()` returns exactly the
 * numbers a viewer will read so the visual-accuracy gate can compare them
 * against the claim ledger character for character.
 *
 * `spec.progress` drives the draw-on animation. It is a pure input: the same
 * spec at the same progress always yields byte-identical SVG.
 */
export class SvgChartRenderer implements ChartRenderer {
  readonly name = 'svg-chart-renderer@1';

  renderSvg(spec: ChartSpec): string {
    return spec.kind === 'line' ? renderLine(spec) : renderBar(spec);
  }

  visibleValues(spec: ChartSpec): string[] {
    const out: string[] = [];
    for (const s of spec.series) {
      for (const p of s.points) out.push(formatValue(p.y, s.unit));
    }
    return out;
  }
}

// ---------------------------------------------------------------------------

/**
 * Padding scales with the canvas. A fixed inset works at 1560×700 and clips the
 * axis labels at 940×720, which is exactly the sort of thing that only shows up
 * once a frame is on screen.
 */
function padFor(w: number, h: number) {
  return {
    top: Math.round(h * 0.07),
    right: Math.round(w * 0.13),
    bottom: Math.round(h * 0.16),
    left: Math.round(w * 0.115),
  };
}

function formatValue(y: number, unit: string): string {
  const abs = Math.abs(y);
  const decimals = abs >= 100 ? 0 : abs >= 10 ? 1 : 2;
  const n = y.toFixed(decimals).replace(/\.0+$/u, (m) => (decimals === 2 ? m : ''));
  if (unit === '%') return `${n}%`;
  if (unit.startsWith('$')) return `$${n}${unit.slice(1)}`;
  return unit ? `${n} ${unit}` : n;
}

function niceBounds(min: number, max: number): { lo: number; hi: number; step: number } {
  if (min === max) return { lo: min - 1, hi: max + 1, step: 1 };
  const span = max - min;
  const padded = span * 0.18;
  let lo = min - padded;
  let hi = max + padded;
  if (min >= 0 && lo < 0) lo = 0;
  const rawStep = (hi - lo) / 4;
  const mag = 10 ** Math.floor(Math.log10(rawStep));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= rawStep) ?? mag * 10;
  lo = Math.floor(lo / step) * step;
  hi = Math.ceil(hi / step) * step;
  return { lo, hi, step };
}

function esc(s: string): string {
  return s.replace(/&/gu, '&amp;').replace(/</gu, '&lt;').replace(/>/gu, '&gt;');
}

/** Cubic ease-out, so the draw decelerates instead of stopping dead. */
function easeOut(t: number): number {
  const c = Math.min(1, Math.max(0, t));
  return 1 - (1 - c) ** 3;
}

function chartFrame(spec: ChartSpec, body: string, axes: string): string {
  const { width: W, height: H, palette: c } = spec;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(spec.yLabel || 'chart')}">
  <defs>
    <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${c.accent}" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="${c.accent}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="barFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${c.accent}"/>
      <stop offset="100%" stop-color="${c.accent2}"/>
    </linearGradient>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="7" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  ${axes}
  ${body}
</svg>`;
}

function axisLayer(spec: ChartSpec, lo: number, hi: number, step: number, xLabels: string[], plotW: number, plotH: number, PAD: ReturnType<typeof padFor>): string {
  const { palette: c } = spec;
  const fs = Math.max(18, Math.round(spec.width * 0.016));
  const rows: string[] = [];
  for (let v = lo; v <= hi + 1e-9; v += step) {
    const y = PAD.top + plotH - ((v - lo) / (hi - lo)) * plotH;
    rows.push(
      `<line x1="${PAD.left}" y1="${y.toFixed(2)}" x2="${PAD.left + plotW}" y2="${y.toFixed(2)}" stroke="${c.grid}" stroke-width="1"/>` +
      `<text x="${PAD.left - 18}" y="${(y + fs * 0.34).toFixed(2)}" text-anchor="end" fill="${c.inkDim}" font-size="${fs}" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(v, spec.series[0]?.unit ?? ''))}</text>`,
    );
  }
  const n = xLabels.length;
  const cols = xLabels.map((label, i) => {
    const x = n === 1 ? PAD.left + plotW / 2 : PAD.left + (i / (n - 1)) * plotW;
    return `<text x="${x.toFixed(2)}" y="${PAD.top + plotH + fs * 1.8}" text-anchor="middle" fill="${c.inkDim}" font-size="${fs}" font-family="var(--mono, ui-monospace, monospace)" letter-spacing="0.06em">${esc(label)}</text>`;
  });
  return `<g>${rows.join('')}${cols.join('')}</g>`;
}

function renderLine(spec: ChartSpec): string {
  const { width: W, height: H, palette: c } = spec;
  const PAD = padFor(W, H);
  const fs = Math.max(18, Math.round(W * 0.016));
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const all = spec.series.flatMap((s) => s.points.map((p) => p.y));
  const { lo, hi, step } = niceBounds(Math.min(...all), Math.max(...all));
  const xLabels = spec.series[0]?.points.map((p) => p.x) ?? [];

  const px = (i: number, n: number) => (n === 1 ? PAD.left + plotW / 2 : PAD.left + (i / (n - 1)) * plotW);
  const py = (v: number) => PAD.top + plotH - ((v - lo) / (hi - lo)) * plotH;

  const t = easeOut(spec.progress);
  const layers = spec.series.map((s, si) => {
    const n = s.points.length;
    const shown = Math.max(1, Math.min(n, Math.ceil(n * t)));
    const partial = n * t - (shown - 1);
    const pts: Array<[number, number]> = [];
    for (let i = 0; i < shown; i += 1) {
      const p = s.points[i]!;
      if (i === shown - 1 && shown < n && shown > 1) {
        const prev = s.points[i - 1]!;
        const f = Math.min(1, Math.max(0, partial));
        pts.push([px(i - 1, n) + (px(i, n) - px(i - 1, n)) * f, py(prev.y + (p.y - prev.y) * f)]);
      } else {
        pts.push([px(i, n), py(p.y)]);
      }
    }
    const d = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
    const areaD = `${d} L${pts[pts.length - 1]![0].toFixed(2)},${(PAD.top + plotH).toFixed(2)} L${pts[0]![0].toFixed(2)},${(PAD.top + plotH).toFixed(2)} Z`;
    const stroke = si === 0 ? c.accent : c.accent2;
    const dots = pts
      .slice(0, shown === n ? n : shown - 1)
      .map(([x, y]) => `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="7" fill="${spec.palette.surface}" stroke="${stroke}" stroke-width="4"/>`)
      .join('');
    const head = pts[pts.length - 1]!;
    const headDot = `<circle cx="${head[0].toFixed(2)}" cy="${head[1].toFixed(2)}" r="11" fill="${stroke}" filter="url(#glow)"/>`;

    // Value label on the final point, revealed once the line has fully drawn.
    // It flips to the left of the head rather than running off the canvas.
    let endLabel = '';
    if (si === 0 && t > 0.94) {
      const last = s.points[n - 1]!;
      const o = ((t - 0.94) / 0.06).toFixed(3);
      const text = formatValue(last.y, s.unit);
      const lf = Math.round(fs * 1.35);
      const lw = Math.max(lf * 3, text.length * lf * 0.66 + lf);
      const lh = Math.round(lf * 1.9);
      const flip = head[0] + 20 + lw > W - 8;
      const lx = flip ? head[0] - 20 - lw : head[0] + 20;
      const ly = Math.min(H - PAD.bottom - lh, Math.max(PAD.top, head[1] - lh / 2));
      endLabel = `<g opacity="${o}"><rect x="${lx.toFixed(2)}" y="${ly.toFixed(2)}" rx="${(lf * 0.35).toFixed(1)}" width="${lw.toFixed(1)}" height="${lh}" fill="${stroke}"/>` +
        `<text x="${(lx + lw / 2).toFixed(2)}" y="${(ly + lh * 0.68).toFixed(2)}" text-anchor="middle" fill="${spec.palette.surface}" font-size="${lf}" font-weight="700" font-family="var(--mono, ui-monospace, monospace)">${esc(text)}</text></g>`;
    }
    return `<g>${si === 0 ? `<path d="${areaD}" fill="url(#areaFill)"/>` : ''}<path d="${d}" fill="none" stroke="${stroke}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>${dots}${headDot}${endLabel}</g>`;
  });

  const legend = spec.series.length > 1
    ? `<g>${spec.series.map((s, i) =>
        `<g transform="translate(${PAD.left + i * Math.round(W * 0.22)}, ${PAD.top - fs})"><rect width="${fs}" height="5" rx="2.5" y="-5" fill="${i === 0 ? c.accent : c.accent2}"/><text x="${fs * 1.6}" y="0" fill="${c.ink}" font-size="${fs}">${esc(s.label)}</text></g>`).join('')}</g>`
    : '';

  // The source stamp is part of the picture, not a caption bolted underneath:
  // if the chart is screenshotted, the provenance travels with it.
  const stamp = `<text x="${PAD.left}" y="${H - Math.round(fs * 0.6)}" fill="${c.inkDim}" font-size="${Math.round(fs * 0.86)}" letter-spacing="0.04em">${esc(`${spec.sourceLabel} · as of ${spec.asOfDate}`)}</text>`;

  return chartFrame(spec, `${layers.join('')}${legend}${stamp}`, axisLayer(spec, lo, hi, step, xLabels, plotW, plotH, PAD));
}

function renderBar(spec: ChartSpec): string {
  const { width: W, height: H, palette: c } = spec;
  const PAD = padFor(W, H);
  const fs = Math.max(18, Math.round(W * 0.016));
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const s = spec.series[0]!;
  const all = s.points.map((p) => p.y);
  const { lo, hi, step } = niceBounds(Math.min(0, ...all), Math.max(...all));
  const n = s.points.length;
  const slot = plotW / n;
  const bw = Math.min(slot * 0.56, W * 0.09);
  const t = easeOut(spec.progress);

  const bars = s.points.map((p, i) => {
    // Bars grow in sequence rather than all at once.
    const local = Math.min(1, Math.max(0, (t * n - i * 0.55) / 0.9));
    const g = easeOut(local);
    const yFull = PAD.top + plotH - ((p.y - lo) / (hi - lo)) * plotH;
    const h = (PAD.top + plotH - yFull) * g;
    const y = PAD.top + plotH - h;
    const x = PAD.left + i * slot + (slot - bw) / 2;
    const highlighted = spec.highlightIndex === i;
    const fill = highlighted ? c.accent : 'url(#barFill)';
    const label = g > 0.85
      ? `<text x="${(x + bw / 2).toFixed(2)}" y="${(y - fs * 0.7).toFixed(2)}" text-anchor="middle" fill="${highlighted ? c.accent : c.ink}" font-size="${Math.round(fs * 1.18)}" font-weight="700" opacity="${((g - 0.85) / 0.15).toFixed(3)}" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(p.y, s.unit))}</text>`
      : '';
    return `<g><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${bw.toFixed(2)}" height="${Math.max(0, h).toFixed(2)}" rx="10" fill="${fill}" ${highlighted ? 'filter="url(#glow)"' : ''}/>${label}</g>`;
  });

  const xLabels = s.points.map((p) => p.x);
  const cols = xLabels.map((label, i) =>
    `<text x="${(PAD.left + i * slot + slot / 2).toFixed(2)}" y="${PAD.top + plotH + fs * 1.8}" text-anchor="middle" fill="${c.inkDim}" font-size="${fs}" font-family="var(--mono, ui-monospace, monospace)" letter-spacing="0.06em">${esc(label)}</text>`).join('');

  const grid: string[] = [];
  for (let v = lo; v <= hi + 1e-9; v += step) {
    const y = PAD.top + plotH - ((v - lo) / (hi - lo)) * plotH;
    grid.push(`<line x1="${PAD.left}" y1="${y.toFixed(2)}" x2="${PAD.left + plotW}" y2="${y.toFixed(2)}" stroke="${c.grid}" stroke-width="1"/>` +
      `<text x="${PAD.left - 18}" y="${(y + fs * 0.34).toFixed(2)}" text-anchor="end" fill="${c.inkDim}" font-size="${fs}" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(v, s.unit))}</text>`);
  }

  const stamp = `<text x="${PAD.left}" y="${H - Math.round(fs * 0.6)}" fill="${c.inkDim}" font-size="${Math.round(fs * 0.86)}" letter-spacing="0.04em">${esc(`${spec.sourceLabel} · as of ${spec.asOfDate}`)}</text>`;

  return chartFrame(spec, `${bars.join('')}${stamp}`, `<g>${grid.join('')}${cols}</g>`);
}
