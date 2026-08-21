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

const PAD = { top: 56, right: 96, bottom: 74, left: 96 };

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

function axisLayer(spec: ChartSpec, lo: number, hi: number, step: number, xLabels: string[], plotW: number, plotH: number): string {
  const { palette: c } = spec;
  const rows: string[] = [];
  for (let v = lo; v <= hi + 1e-9; v += step) {
    const y = PAD.top + plotH - ((v - lo) / (hi - lo)) * plotH;
    rows.push(
      `<line x1="${PAD.left}" y1="${y.toFixed(2)}" x2="${PAD.left + plotW}" y2="${y.toFixed(2)}" stroke="${c.grid}" stroke-width="1"/>` +
      `<text x="${PAD.left - 18}" y="${(y + 7).toFixed(2)}" text-anchor="end" fill="${c.inkDim}" font-size="24" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(v, spec.series[0]?.unit ?? ''))}</text>`,
    );
  }
  const n = xLabels.length;
  const cols = xLabels.map((label, i) => {
    const x = n === 1 ? PAD.left + plotW / 2 : PAD.left + (i / (n - 1)) * plotW;
    return `<text x="${x.toFixed(2)}" y="${PAD.top + plotH + 44}" text-anchor="middle" fill="${c.inkDim}" font-size="24" font-family="var(--mono, ui-monospace, monospace)" letter-spacing="0.06em">${esc(label)}</text>`;
  });
  return `<g>${rows.join('')}${cols.join('')}</g>`;
}

function renderLine(spec: ChartSpec): string {
  const { width: W, height: H, palette: c } = spec;
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
    let endLabel = '';
    if (si === 0 && t > 0.94) {
      const last = s.points[n - 1]!;
      const o = ((t - 0.94) / 0.06).toFixed(3);
      endLabel = `<g opacity="${o}"><rect x="${(head[0] + 20).toFixed(2)}" y="${(head[1] - 32).toFixed(2)}" rx="10" width="${Math.max(96, formatValue(last.y, s.unit).length * 22)}" height="62" fill="${stroke}"/>` +
        `<text x="${(head[0] + 36).toFixed(2)}" y="${(head[1] + 10).toFixed(2)}" fill="${spec.palette.surface}" font-size="34" font-weight="700" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(last.y, s.unit))}</text></g>`;
    }
    return `<g>${si === 0 ? `<path d="${areaD}" fill="url(#areaFill)"/>` : ''}<path d="${d}" fill="none" stroke="${stroke}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>${dots}${headDot}${endLabel}</g>`;
  });

  const legend = spec.series.length > 1
    ? `<g>${spec.series.map((s, i) =>
        `<g transform="translate(${PAD.left + i * 320}, ${PAD.top - 26})"><rect width="26" height="6" rx="3" y="-6" fill="${i === 0 ? c.accent : c.accent2}"/><text x="40" y="0" fill="${c.ink}" font-size="26">${esc(s.label)}</text></g>`).join('')}</g>`
    : '';

  const stamp = `<text x="${PAD.left}" y="${H - 16}" fill="${c.inkDim}" font-size="21" letter-spacing="0.04em">${esc(`${spec.sourceLabel} · as of ${spec.asOfDate}`)}</text>`;
  const yTitle = spec.yLabel ? `<text x="${PAD.left}" y="${PAD.top - 26}" fill="${c.inkDim}" font-size="24" letter-spacing="0.12em">${esc(spec.yLabel.toUpperCase())}</text>` : '';

  return chartFrame(spec, `${layers.join('')}${legend}${stamp}`, `${axisLayer(spec, lo, hi, step, xLabels, plotW, plotH)}${yTitle}`);
}

function renderBar(spec: ChartSpec): string {
  const { width: W, height: H, palette: c } = spec;
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const s = spec.series[0]!;
  const all = s.points.map((p) => p.y);
  const { lo, hi, step } = niceBounds(Math.min(0, ...all), Math.max(...all));
  const n = s.points.length;
  const slot = plotW / n;
  const bw = Math.min(slot * 0.56, 150);
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
      ? `<text x="${(x + bw / 2).toFixed(2)}" y="${(y - 20).toFixed(2)}" text-anchor="middle" fill="${highlighted ? c.accent : c.ink}" font-size="30" font-weight="700" opacity="${((g - 0.85) / 0.15).toFixed(3)}" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(p.y, s.unit))}</text>`
      : '';
    return `<g><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${bw.toFixed(2)}" height="${Math.max(0, h).toFixed(2)}" rx="10" fill="${fill}" ${highlighted ? 'filter="url(#glow)"' : ''}/>${label}</g>`;
  });

  const xLabels = s.points.map((p) => p.x);
  const cols = xLabels.map((label, i) =>
    `<text x="${(PAD.left + i * slot + slot / 2).toFixed(2)}" y="${PAD.top + plotH + 44}" text-anchor="middle" fill="${c.inkDim}" font-size="24" font-family="var(--mono, ui-monospace, monospace)" letter-spacing="0.06em">${esc(label)}</text>`).join('');

  const grid: string[] = [];
  for (let v = lo; v <= hi + 1e-9; v += step) {
    const y = PAD.top + plotH - ((v - lo) / (hi - lo)) * plotH;
    grid.push(`<line x1="${PAD.left}" y1="${y.toFixed(2)}" x2="${PAD.left + plotW}" y2="${y.toFixed(2)}" stroke="${c.grid}" stroke-width="1"/>` +
      `<text x="${PAD.left - 18}" y="${(y + 7).toFixed(2)}" text-anchor="end" fill="${c.inkDim}" font-size="24" font-family="var(--mono, ui-monospace, monospace)">${esc(formatValue(v, s.unit))}</text>`);
  }

  const stamp = `<text x="${PAD.left}" y="${H - 16}" fill="${c.inkDim}" font-size="21" letter-spacing="0.04em">${esc(`${spec.sourceLabel} · as of ${spec.asOfDate}`)}</text>`;
  const yTitle = spec.yLabel ? `<text x="${PAD.left}" y="${PAD.top - 26}" fill="${c.inkDim}" font-size="24" letter-spacing="0.12em">${esc(spec.yLabel.toUpperCase())}</text>` : '';

  return chartFrame(spec, `${bars.join('')}${stamp}`, `<g>${grid.join('')}${cols}</g>${yTitle}`);
}
