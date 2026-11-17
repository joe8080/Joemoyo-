// Stick-man POV drama renderer. Runs in a browser page; window.TL is the compiled timeline.
// window.drawFrame(t) paints the frame for time t (seconds) onto the 1080x1920 canvas.
(() => {
  const W = 1080, H = 1920;
  const cv = document.getElementById('c');
  const ctx = cv.getContext('2d');
  let INK = '#151515', SKIN = '#fff';
  const PAPER = '#f6f1e7', YEL = '#FFD60A', RED = '#ef4444', GRN = '#22c55e', BLU = '#3b82f6';
  const FONT = 'Inter, "DejaVu Sans", sans-serif';

  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = (k) => { k = clamp(k); return k * k * (3 - 2 * k); };
  const easeOut = (k) => 1 - Math.pow(1 - clamp(k), 3);
  const backOut = (k) => { k = clamp(k); const c = 1.70158; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const money = (v) => '£' + Math.round(v).toLocaleString('en-GB');

  // "boiling line" wobble: every stroke gets a little jitter that re-rolls 10x a second
  let boil = 0, strokeN = 0;
  const jit = (amp) => { strokeN++; return (hash(strokeN * 13.37 + boil * 7.77) - 0.5) * 2 * amp; };

  function line(x1, y1, x2, y2, w, col = INK, wob = 3) {
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(x1 + jit(wob * 0.4), y1 + jit(wob * 0.4));
    ctx.quadraticCurveTo((x1 + x2) / 2 + jit(wob), (y1 + y2) / 2 + jit(wob), x2 + jit(wob * 0.4), y2 + jit(wob * 0.4));
    ctx.stroke();
  }
  function circ(x, y, r, w, fill, col = INK) {
    ctx.beginPath();
    ctx.ellipse(x + jit(1.2), y + jit(1.2), Math.max(0.1, r + jit(1.2)), Math.max(0.1, r + jit(1.2)), 0, 0, 7);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (w) { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke(); }
  }
  function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
  function font(px, weight = 800, italic = false) { ctx.font = `${italic ? 'italic ' : ''}${weight} ${px}px ${FONT}`; }
  function text(s, x, y, col = INK, align = 'left', base = 'alphabetic') {
    ctx.fillStyle = col; ctx.textAlign = align; ctx.textBaseline = base; ctx.fillText(s, x, y);
  }
  function wrap(words, maxW) {
    const sp = ctx.measureText(' ').width, lines = [[]];
    let w = 0;
    words.forEach((wd, i) => {
      const ww = ctx.measureText(wd.t).width;
      if (w + ww > maxW && lines.at(-1).length) { lines.push([]); w = 0; }
      lines.at(-1).push({ ...wd, i, ww });
      w += ww + sp;
    });
    return lines.map((ln) => ({ ws: ln, w: ln.reduce((s, x) => s + x.ww, 0) + sp * (ln.length - 1), sp }));
  }
  const plain = (s) => s.split(/\s+/).map((t) => ({ t }));

  // ───────────────────────── stick figure ─────────────────────────
  // arm angles in degrees from "hanging straight down": [upperL, foreL, upperR, foreR]; + = away from body
  const POSES = {
    idle: [10, 4, 10, 4], shrug: [38, 140, 38, 140], handsUp: [128, 160, 128, 160], crossed: [24, -105, 24, -105],
    beg: [30, -150, 30, -150], facepalm: [10, 4, 34, -168], wave: [10, 4, 125, 172], hips: [52, -38, 52, -38],
    think: [18, -85, 26, -160], pointUp: [10, 4, 72, 178], open: [62, 84, 62, 84], cheer: [158, 176, 158, 176],
  };
  const EMO = {
    neutral: { eye: 'dot', mouth: 'flat' }, happy: { eye: 'dot', mouth: 'smile' }, laugh: { eye: 'arc', mouth: 'grin' },
    smug: { eye: 'half', mouth: 'smirk', brow: 'raise' }, angry: { eye: 'dot', mouth: 'frown', brow: 'angry', extra: 'vein' },
    sad: { eye: 'dot', mouth: 'frown', brow: 'sad' }, cry: { eye: 'shut', mouth: 'frown', brow: 'sad', extra: 'tears' },
    shock: { eye: 'wide', mouth: 'o', extra: 'sweat' }, nervous: { eye: 'dot', mouth: 'wavy', brow: 'sad', extra: 'sweat' },
    awkward: { eye: 'dot', mouth: 'flat', extra: 'sweat' },
  };

  function actorState(shot, name, def, t) {
    let cur = { emo: def.emo || 'neutral', pose: def.pose || 'idle', at: -9 }, prev = cur, talk = false;
    for (const b of shot.beats || []) {
      if (b.start > t) break;
      let ch = null;
      if (b.who === name && (b.emo || b.pose)) ch = b;
      if (b.react && b.react[name]) ch = b.react[name];
      if (ch) { prev = cur; cur = { emo: ch.emo || cur.emo, pose: ch.pose || cur.pose, at: b.start }; }
      talk = b.who === name && t < b.start + (b.talkDur || 0);
    }
    return { cur, prev, k: ease((t - cur.at) / 0.2), talk };
  }

  function figure(a, st, t) {
    const h = a.h || 900, cx = a.px ?? a.x * W, lw = h * 0.021, r = h * 0.125;
    const emo = st.cur.emo, since = t - st.cur.at;
    const jump = emo === 'shock' ? -h * 0.035 * Math.sin(clamp(since / 0.32) * Math.PI) : 0;
    const fy = (a.py ?? (a.y || 0.7) * H) + jump;
    const bob = Math.sin(t * 2.1 + (a.seed || 0) * 2) * h * 0.004 + (st.talk ? Math.sin(t * 15) * h * 0.004 : 0);
    const droop = emo === 'sad' || emo === 'cry' ? h * 0.014 : 0;
    const hy = fy - h + r + bob + droop, neck = hy + r, sh = neck + h * 0.035, hip = neck + h * 0.34;
    const tremble = emo === 'angry' || emo === 'nervous' ? Math.sin(t * 46) * h * 0.003 : 0;

    line(cx, hip, cx - h * 0.085, fy, lw); line(cx - h * 0.085, fy, cx - h * 0.14, fy, lw);
    line(cx, hip, cx + h * 0.085, fy, lw); line(cx + h * 0.085, fy, cx + h * 0.14, fy, lw);
    line(cx + tremble, neck, cx, hip, lw);

    if (a.look === 'tie') {
      ctx.fillStyle = a.accent || BLU; ctx.beginPath();
      ctx.moveTo(cx, neck + h * 0.01); ctx.lineTo(cx + h * 0.028, neck + h * 0.05); ctx.lineTo(cx + h * 0.02, neck + h * 0.16);
      ctx.lineTo(cx, neck + h * 0.19); ctx.lineTo(cx - h * 0.02, neck + h * 0.16); ctx.lineTo(cx - h * 0.028, neck + h * 0.05);
      ctx.closePath(); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.4; ctx.stroke();
    }

    const A = POSES[st.cur.pose] || POSES.idle, B = POSES[st.prev.pose] || POSES.idle;
    const ang = A.map((v, i) => lerp(B[i], v, st.k));
    if (st.cur.pose === 'wave') ang[3] += Math.sin(t * 12) * 16;
    if (st.cur.pose === 'beg') { ang[1] += Math.sin(t * 9) * 5; ang[3] += Math.sin(t * 9) * 5; }
    const seg = h * 0.168;
    for (const side of [-1, 1]) {
      const u = (ang[side < 0 ? 0 : 2] * Math.PI) / 180, f = (ang[side < 0 ? 1 : 3] * Math.PI) / 180;
      const ex = cx + side * Math.sin(u) * seg, ey = sh + Math.cos(u) * seg;
      const hx = ex + side * Math.sin(f) * seg + tremble, hy2 = ey + Math.cos(f) * seg;
      line(cx, sh, ex, ey, lw); line(ex, ey, hx, hy2, lw); circ(hx, hy2, h * 0.026, 0, INK);
    }

    circ(cx + tremble, hy, r, lw, SKIN);
    face(cx + tremble, hy, r, emo, st.talk, t, a, since);
    headwear(cx + tremble, hy, r, a, lw);
  }

  function face(cx, cy, r, emo, talk, t, a, since) {
    const E = EMO[emo] || EMO.neutral;
    const ex = r * 0.38, ey = cy - r * 0.1, er = r * 0.095, lw = r * 0.095;
    const blink = (t + (a.seed || 0) * 1.3) % 3.4 < 0.11;
    ctx.lineCap = 'round';
    for (const s of [-1, 1]) {
      const x = cx + s * ex;
      if (a.look === 'shades') continue;
      if (E.eye === 'wide') { circ(x, ey, er * 2.4, lw * 0.7, '#fff'); circ(x, ey, er * 0.75, 0, INK); }
      else if (E.eye === 'arc') { ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(x, ey + er, er * 1.9, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); }
      else if (E.eye === 'shut' || blink) line(x - er * 1.6, ey, x + er * 1.6, ey, lw, INK, 0.5);
      else { circ(x, ey, er * 1.15, 0, INK); if (E.eye === 'half') line(x - er * 2, ey - er * 0.9, x + er * 2, ey - er * 0.9, lw * 1.1, INK, 0.5); }
      const by = ey - r * 0.3;
      if (E.brow === 'angry') line(x + s * er * 2.6, by - r * 0.1, x - s * er * 1.8, by + r * 0.13, lw, INK, 0.5);
      if (E.brow === 'sad') line(x + s * er * 2.6, by + r * 0.1, x - s * er * 1.8, by - r * 0.1, lw, INK, 0.5);
      if (E.brow === 'raise') line(x - er * 2.2, by - (s > 0 ? r * 0.14 : -r * 0.02), x + er * 2.2, by - (s > 0 ? r * 0.2 : -r * 0.02), lw, INK, 0.5);
    }
    if (a.look === 'shades') {
      ctx.fillStyle = INK; rr(cx - ex - er * 3.4, ey - er * 2.2, ex * 2 + er * 6.8, er * 4.6, er * 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,.35)'; rr(cx - ex - er * 2, ey - er * 1.4, er * 2.4, er * 1, er); ctx.fill();
    }
    if (a.look === 'glasses') {
      for (const s of [-1, 1]) circ(cx + s * ex, ey, er * 3, lw * 0.75, 'rgba(255,255,255,.01)', a.accent || INK);
      line(cx - ex + er * 3, ey, cx + ex - er * 3, ey, lw * 0.75, a.accent || INK, 0.3);
    }

    const my = cy + r * 0.45, mw = r * 0.5;
    const open = talk ? Math.abs(Math.sin(t * 17)) : 0;
    ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.fillStyle = INK;
    if (talk && open > 0.35 && E.mouth !== 'o') {
      ctx.beginPath(); ctx.ellipse(cx, my, mw * 0.55, mw * (0.18 + open * 0.42), 0, 0, 7); ctx.fill();
    } else if (E.mouth === 'flat') line(cx - mw * 0.7, my, cx + mw * 0.7, my, lw, INK, 0.5);
    else if (E.mouth === 'smile') { ctx.beginPath(); ctx.moveTo(cx - mw, my - mw * 0.2); ctx.quadraticCurveTo(cx, my + mw * 0.8, cx + mw, my - mw * 0.2); ctx.stroke(); }
    else if (E.mouth === 'frown') { ctx.beginPath(); ctx.moveTo(cx - mw * 0.9, my + mw * 0.35); ctx.quadraticCurveTo(cx, my - mw * 0.5, cx + mw * 0.9, my + mw * 0.35); ctx.stroke(); }
    else if (E.mouth === 'smirk') { ctx.beginPath(); ctx.moveTo(cx - mw * 0.6, my + mw * 0.1); ctx.quadraticCurveTo(cx + mw * 0.4, my + mw * 0.55, cx + mw * 1.05, my - mw * 0.4); ctx.stroke(); }
    else if (E.mouth === 'o') { const p = 1 + 0.12 * Math.sin(t * 20) * Math.exp(-since * 3); ctx.beginPath(); ctx.ellipse(cx, my + mw * 0.1, mw * 0.42 * p, mw * 0.62 * p, 0, 0, 7); ctx.fill(); }
    else if (E.mouth === 'grin') { ctx.beginPath(); ctx.moveTo(cx - mw, my - mw * 0.25); ctx.quadraticCurveTo(cx, my + mw * 1.5, cx + mw, my - mw * 0.25); ctx.closePath(); ctx.fill(); }
    else if (E.mouth === 'wavy') { ctx.beginPath(); for (let i = 0; i <= 12; i++) { const x = cx - mw + (i / 12) * mw * 2, y = my + Math.sin(i * 1.6 + t * 10) * mw * 0.16; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }

    if (E.extra === 'sweat') {
      const p = (t * 0.7 + (a.seed || 0) * 0.3) % 1, x = cx + r * 0.78, y = cy - r * 0.55 + p * r * 0.7;
      ctx.fillStyle = '#38bdf8'; ctx.globalAlpha = 1 - p * 0.7; ctx.beginPath();
      ctx.moveTo(x, y - r * 0.2); ctx.quadraticCurveTo(x + r * 0.16, y + r * 0.08, x, y + r * 0.12); ctx.quadraticCurveTo(x - r * 0.16, y + r * 0.08, x, y - r * 0.2);
      ctx.fill(); ctx.globalAlpha = 1;
    }
    if (E.extra === 'tears') for (const s of [-1, 1]) {
      const x = cx + s * ex; ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = lw * 1.5; ctx.beginPath(); ctx.moveTo(x, ey + er * 2);
      for (let i = 1; i <= 6; i++) ctx.lineTo(x + Math.sin(i * 1.3 + t * 9) * er * 0.8, ey + er * 2 + (i / 6) * r * 0.8);
      ctx.stroke();
    }
    if (E.extra === 'vein') {
      const x = cx + r * 0.62, y = cy - r * 0.68, q = r * 0.11;
      for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) line(x + dx * q * 0.5, y + dy * q * 0.5, x + dx * q * 1.6, y + dy * q * 0.5, lw * 0.9, RED, 0.5);
      for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) line(x + dx * q * 0.5, y + dy * q * 0.5, x + dx * q * 0.5, y + dy * q * 1.6, lw * 0.9, RED, 0.5);
    }
  }

  function headwear(cx, hy, r, a, lw) {
    const col = a.accent || RED;
    if (a.look === 'cap') {
      ctx.fillStyle = col; ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.6;
      ctx.beginPath(); ctx.arc(cx, hy, r * 1.05, Math.PI * 1.08, Math.PI * 1.92); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(cx, hy - r * 0.36, r * 0.88, r * 0.16, 0, 0, 7); ctx.fill(); ctx.stroke();
    }
    if (a.look === 'hair') {
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(cx, hy, r * 1.06, Math.PI * 1.0, Math.PI * 2.0);
      ctx.quadraticCurveTo(cx + r * 0.3, hy - r * 0.75, cx - r * 0.2, hy - r * 0.55); ctx.quadraticCurveTo(cx - r * 0.7, hy - r * 0.4, cx - r * 1.06, hy);
      ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.6; ctx.stroke();
    }
  }

  // ───────────────────────── backgrounds ─────────────────────────
  const TINT = { pub: '#f4e4c8', office: '#e3ecf4', room: '#ebe5f5', street: '#e6f0e2' };
  function background(name, t) {
    ctx.fillStyle = TINT[name] || PAPER; ctx.fillRect(-300, -300, W + 600, H + 600);
    const c = 'rgba(21,21,21,.26)', w = 7;
    const fl = 0.7 * H;
    ctx.fillStyle = 'rgba(21,21,21,.05)'; ctx.fillRect(-300, fl, W + 600, H);
    line(-300, fl, W + 300, fl, w, c, 2);
    const box = (x, y, bw, bh) => { line(x, y, x + bw, y, w, c, 2); line(x + bw, y, x + bw, y + bh, w, c, 2); line(x + bw, y + bh, x, y + bh, w, c, 2); line(x, y + bh, x, y, w, c, 2); };
    if (name === 'pub') {
      for (const sy of [600, 800]) {
        line(40, sy, 400, sy, w, c, 2);
        for (let i = 0; i < 5; i++) { const x = 70 + i * 68, bh = 90 + hash(i + sy) * 50; box(x, sy - bh, 34, bh); line(x + 17, sy - bh, x + 17, sy - bh - 34, w * 1.6, c, 1); }
      }
      for (const lx of [760, 960]) {
        line(lx, -20, lx, 390, w * 0.7, c, 1);
        ctx.fillStyle = 'rgba(255,214,10,.22)'; ctx.beginPath(); ctx.arc(lx, 470, 150 + Math.sin(t * 3 + lx) * 6, 0, 7); ctx.fill();
        ctx.fillStyle = 'rgba(21,21,21,.3)'; ctx.beginPath(); ctx.moveTo(lx - 70, 460); ctx.lineTo(lx + 70, 460); ctx.lineTo(lx + 30, 380); ctx.lineTo(lx - 30, 380); ctx.closePath(); ctx.fill();
      }
      for (const rr2 of [110, 75, 38]) circ(880, 860, rr2, w * 0.8, null, c);
      // table edge + pint in front of you
      ctx.fillStyle = '#e2cfa9'; ctx.fillRect(-300, 1640, W + 600, 600); line(-300, 1640, W + 300, 1640, w * 1.3, 'rgba(21,21,21,.45)', 2);
      ctx.fillStyle = 'rgba(245,180,40,.75)'; rr(110, 1490, 110, 150, 10); ctx.fill();
      ctx.fillStyle = '#fff'; rr(104, 1462, 122, 40, 18); ctx.fill();
      ctx.strokeStyle = 'rgba(21,21,21,.6)'; ctx.lineWidth = 7; rr(108, 1466, 114, 176, 12); ctx.stroke();
    }
    if (name === 'office') {
      box(650, 430, 360, 470); line(830, 430, 830, 900, w, c, 1); line(650, 665, 1010, 665, w, c, 1);
      for (let i = 0; i < 4; i++) { const bh = 90 + hash(i * 3.3) * 110; ctx.fillStyle = 'rgba(21,21,21,.09)'; ctx.fillRect(668 + i * 84, 893 - bh, 64, bh); }
      box(70, 500, 330, 250);
      for (let i = 0; i < 5; i++) { ctx.fillStyle = 'rgba(21,21,21,.16)'; ctx.fillRect(100 + i * 58, 720 - (35 + i * 32), 36, 35 + i * 32); }
      line(60, fl, 60, fl - 150, w, c, 1); box(20, fl - 150, 90, 12);
      for (let i = 0; i < 5; i++) line(65, fl - 160, 65 + (i - 2) * 46, fl - 300 - hash(i) * 70, w, 'rgba(34,150,80,.5)', 4);
      ctx.fillStyle = '#cfd9e3'; ctx.fillRect(-300, 1660, W + 600, 600); line(-300, 1660, W + 300, 1660, w * 1.3, 'rgba(21,21,21,.45)', 2);
    }
    if (name === 'room') {
      box(90, 440, 300, 380); line(240, 440, 240, 820, w, c, 1);
      circ(310, 540, 44, 0, 'rgba(255,214,10,.5)');
      rr(640, 1090, 480, 250, 40); ctx.strokeStyle = c; ctx.lineWidth = w; ctx.stroke(); rr(640, 960, 480, 180, 40); ctx.stroke();
    }
    if (name === 'street') {
      let x = -40;
      for (let i = 0; x < W + 100; i++) { const bw = 150 + hash(i * 1.7) * 130, bh = 300 + hash(i * 2.9) * 420; box(x, fl - bh, bw, bh);
        for (let wy = fl - bh + 50; wy < fl - 90; wy += 110) for (let wx = x + 30; wx < x + bw - 50; wx += 70) { ctx.fillStyle = 'rgba(21,21,21,.08)'; ctx.fillRect(wx, wy, 36, 54); }
        x += bw; }
      line(930, fl, 930, 560, w * 1.4, c, 1); line(930, 560, 860, 540, w * 1.4, c, 1);
      ctx.fillStyle = 'rgba(255,214,10,.3)'; ctx.beginPath(); ctx.arc(850, 560, 70, 0, 7); ctx.fill();
      for (const [cx2, cy2] of [[220, 360], [700, 300]]) { ctx.fillStyle = 'rgba(255,255,255,.8)'; for (const [dx, rr3] of [[-60, 44], [0, 62], [66, 46]]) { ctx.beginPath(); ctx.arc(cx2 + dx + Math.sin(t * 0.2) * 20, cy2, rr3, 0, 7); ctx.fill(); } }
    }
  }

  // ───────────────────────── POV hands ─────────────────────────
  function handState(shot, t) {
    let mode = shot.hands || 'idle', at = -9;
    for (const b of shot.beats || []) { if (b.start > t) break; if (b.hands) { mode = b.hands; at = b.start; } }
    return { mode, since: t - at };
  }
  function povArm(x1, y1, x2, y2, r = 64) { line(x1, y1, x2, y2, 46, INK, 3); circ(x2, y2, r, 13, '#fff'); }
  function povHands(mode, since, t, shot) {
    if (mode === 'none') return;
    const by = Math.sin(t * 1.7) * 9, sh = mode === 'fists' ? Math.sin(t * 44) * 6 : 0;
    const lift = mode === 'fists' ? -90 : 0;
    if (mode === 'phone') {
      ctx.save(); ctx.translate(540, 1790 + by); ctx.rotate(-0.06 + Math.sin(t * 1.1) * 0.01);
      ctx.fillStyle = '#111'; rr(-150, -190, 300, 520, 38); ctx.fill();
      ctx.fillStyle = '#bfdbfe'; rr(-134, -172, 268, 480, 26); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,.6)'; for (let i = 0; i < 3; i++) { rr(-110, -140 + i * 62, 220 - i * 40, 34, 12); ctx.fill(); }
      ctx.restore();
      povArm(40, H + 60, 372, 1770 + by, 54); povArm(W - 40, H + 60, 708, 1760 + by, 54);
      return;
    }
    povArm(60, H + 60, 300 + sh, 1730 + by + lift);
    if (mode === 'paper') {
      const k = backOut(since / 0.45), d = shot.paper || {};
      const px = 770, py = lerp(2300, 1040, k);
      line(W - 60, H + 60, px + 60, py + 260, 46, INK, 3);
      ctx.save(); ctx.translate(px, py); ctx.rotate(0.07 + Math.sin(t * 2) * 0.012);
      ctx.fillStyle = 'rgba(0,0,0,.25)'; rr(-196, -246, 420, 540, 10); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.strokeStyle = INK; ctx.lineWidth = 9; rr(-210, -260, 420, 540, 10); ctx.fill(); ctx.stroke();
      font(42, 900); text(d.title || 'CONTRACT', 0, -190, INK, 'center');
      line(-170, -165, 170, -165, 6, INK, 1);
      font(28, 600); (d.lines || []).forEach((l, i) => text(l, -170, -110 + i * 46, INK));
      for (let i = 0; i < 4; i++) line(-170, 10 + i * 40, 170 - (i === 3 ? 120 : 0), 10 + i * 40, 5, 'rgba(21,21,21,.28)', 1);
      font(24, 600); text('Signed:', -170, 222, '#666');
      ctx.strokeStyle = BLU; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-60, 222);
      for (let i = 1; i <= 16; i++) ctx.lineTo(-60 + i * 13, 222 - Math.sin(i * 1.9) * 26 * (1 - i / 22) - 8);
      ctx.stroke();
      font(30, 800, true); text(d.sign || '', 150, 180, BLU, 'right');
      ctx.restore();
      circ(px + 60, py + 262, 64, 13, '#fff');
    } else povArm(W - 60, H + 60, W - 300 - sh, 1730 + by + lift);
  }

  // ───────────────────────── phone close-up ─────────────────────────
  const PH = { x: 170, y: 362, w: 740, h: 1150 };
  const SW = PH.w - 52, SH = PH.h - 52;

  function drawPhone(shot, t) {
    const lt = t - shot.start, d = shot.data || {};
    const g = ctx.createRadialGradient(W / 2, 900, 200, W / 2, 900, 1300);
    g.addColorStop(0, '#ddd5c5'); g.addColorStop(1, '#a89f8f');
    ctx.fillStyle = g; ctx.fillRect(-300, -300, W + 600, H + 600);
    const off = (1 - easeOut(lt / 0.28)) * 420;
    ctx.save(); ctx.translate(W / 2, 915 + off); ctx.rotate(Math.sin(t * 0.9) * 0.007); ctx.translate(-W / 2, -915 + Math.sin(t * 1.3) * 6);
    line(-40, H + 80, PH.x + 20, PH.y + PH.h - 210, 50, INK, 3);
    line(W + 40, H + 80, PH.x + PH.w - 20, PH.y + PH.h - 210, 50, INK, 3);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; rr(PH.x + 14, PH.y + 18, PH.w, PH.h, 74); ctx.fill();
    ctx.fillStyle = '#111'; rr(PH.x, PH.y, PH.w, PH.h, 74); ctx.fill();
    ctx.save(); rr(PH.x + 26, PH.y + 26, SW, SH, 52); ctx.clip(); ctx.translate(PH.x + 26, PH.y + 26);
    const hold = strokeN; strokeN = 9000; // keep UI text steady: isolate jitter stream
    ({ bank: appBank, chat: appChat, feed: appFeed, portfolio: appPortfolio, lock: appLock }[shot.app] || appLock)(d, lt, t);
    strokeN = hold;
    ctx.fillStyle = '#111'; rr(SW / 2 - 70, 14, 140, 36, 18); ctx.fill();
    ctx.restore();
    // thumbs
    let tx = PH.x + PH.w + 6, ty = PH.y + PH.h - 300;
    if (d.sell) {
      const k = ease((lt - d.sell.at) / 0.7) * (1 - ease((lt - d.sell.at - d.sell.dur) / 0.5));
      tx = lerp(tx, PH.x + 26 + SW * 0.74, k) + Math.sin(t * 38) * 5 * k; ty = lerp(ty, PH.y + 26 + 1010, k) + Math.cos(t * 31) * 5 * k;
    }
    circ(PH.x - 6, PH.y + PH.h - 380, 62, 13, '#fff'); circ(tx, ty, 62, 13, '#fff');
    ctx.restore();
  }

  function statusBar(col, time = '21:47') {
    font(26, 700); text(time, 34, 46, col);
    ctx.strokeStyle = col; ctx.lineWidth = 3; rr(SW - 86, 24, 50, 24, 7); ctx.stroke(); ctx.fillStyle = col; rr(SW - 82, 28, 30, 16, 4); ctx.fill();
  }

  function appBank(d, lt) {
    ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, SW, SH); statusBar('#fff');
    circ(70, 130, 34, 0, '#fb7185'); font(34, 900); text('£', 70, 143, '#fff', 'center');
    font(38, 800); text('PiggyBank', 120, 144, '#fff');
    font(28, 600); text('Current account', 40, 250, '#94a3b8');
    const k = ease((lt - d.at) / d.dur), v = lerp(d.from, d.to, k), drop = d.to < d.from;
    const sc = 1 + 0.06 * Math.sin(clamp((lt - d.at - d.dur) / 0.3) * Math.PI);
    ctx.save(); ctx.translate(40, 350); ctx.scale(sc, sc);
    font(104, 900); text(money(v) + '.00', 0, 0, k > 0 && drop ? `rgb(${lerp(255, 248, k)},${lerp(255, 113, k)},${lerp(255, 113, k)})` : '#fff');
    ctx.restore();
    const rows = [['Salary', '+£1,850.00', '#4ade80'], ['Rent', '−£725.00', '#e2e8f0'], ['Food shop', '−£64.20', '#e2e8f0']];
    let y = 470;
    if (lt > d.at) {
      const s = backOut((lt - d.at) / 0.35);
      ctx.save(); ctx.translate(SW / 2, y + 60); ctx.scale(s, s);
      ctx.fillStyle = '#7f1d1d'; rr(-SW / 2 + 30, -60, SW - 60, 120, 28); ctx.fill();
      font(32, 800); text('Sent to ' + d.payee, -SW / 2 + 64, -6, '#fff'); font(24, 600); text('Just now · Bank transfer', -SW / 2 + 64, 32, '#fca5a5');
      font(36, 900); text('−' + money(d.from - d.to), SW / 2 - 60, 12, '#fecaca', 'right');
      ctx.restore(); y += 140;
    }
    rows.forEach(([a, b, c]) => { ctx.fillStyle = '#1e293b'; rr(30, y, SW - 60, 104, 26); ctx.fill(); font(30, 700); text(a, 64, y + 62, '#e2e8f0'); font(32, 800); text(b, SW - 60, y + 63, c, 'right'); y += 120; });
  }

  function appChat(d, lt, t) {
    ctx.fillStyle = '#eef2f6'; ctx.fillRect(0, 0, SW, SH);
    ctx.fillStyle = '#0f766e'; ctx.fillRect(0, 0, SW, 170); statusBar('#fff');
    circ(74, 114, 36, 0, '#fff'); circ(62, 108, 4, 0, INK); circ(86, 108, 4, 0, INK); line(62, 124, 86, 124, 4, INK, 0);
    font(36, 800); text(d.name, 128, 110, '#fff'); font(24, 600); text(d.status || 'online', 128, 144, '#a7f3d0');
    let y = 210;
    font(32, 600);
    for (const m of d.messages || []) {
      const lines = wrap(plain(m.text), 430), bw = Math.max(...lines.map((l) => l.w)) + 56, bh = lines.length * 44 + 36;
      const me = m.from === 'me', x = me ? SW - 28 - bw : 28;
      if (lt >= m.at) {
        const s = backOut((lt - m.at) / 0.22);
        ctx.save(); ctx.translate(me ? x + bw : x, y + bh); ctx.scale(s, s); ctx.translate(me ? -bw : 0, -bh);
        ctx.fillStyle = me ? '#2563eb' : '#fff'; rr(0, 0, bw, bh, 30); ctx.fill();
        font(32, 600); lines.forEach((l, i) => text(l.ws.map((w) => w.t).join(' '), 28, 52 + i * 44, me ? '#fff' : INK));
        ctx.restore();
        if (m.seenAt != null && lt >= m.seenAt) { font(24, 700); text('Seen ✓✓', SW - 34, y + bh + 34, '#2563eb', 'right'); font(32, 600); }
      }
      y += bh + (m.seenAt != null ? 58 : 16);
    }
    for (const ty of d.typing || []) if (lt >= ty.at && lt < ty.at + ty.dur) {
      ctx.fillStyle = '#fff'; rr(28, y, 150, 76, 30); ctx.fill();
      for (let i = 0; i < 3; i++) circ(66 + i * 36, y + 38 - Math.max(0, Math.sin(t * 9 - i * 0.9)) * 12, 10, 0, '#94a3b8');
    }
    ctx.fillStyle = '#fff'; ctx.fillRect(0, SH - 120, SW, 120); ctx.fillStyle = '#e2e8f0'; rr(28, SH - 96, SW - 56, 68, 34); ctx.fill();
    font(28, 600); text('Message…', 60, SH - 52, '#94a3b8');
  }

  function appFeed(d, lt, t) {
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, SW, SH); statusBar(INK);
    font(40, 900, true); text('snapfeed', SW / 2, 118, INK, 'center');
    circ(64, 190, 34, 6, '#fde68a', '#e11d48'); font(30, 800); text(d.user, 116, 186, INK); font(24, 600); text(d.place || '', 116, 218, '#64748b');
    const iy = 244, ih = 600;
    ctx.save(); ctx.beginPath(); ctx.rect(0, iy, SW, ih); ctx.clip();
    const sky = ctx.createLinearGradient(0, iy, 0, iy + ih); sky.addColorStop(0, '#38bdf8'); sky.addColorStop(0.62, '#fde68a'); ctx.fillStyle = sky; ctx.fillRect(0, iy, SW, ih);
    circ(600, iy + 110, 64, 0, '#fff7c2');
    ctx.fillStyle = '#0ea5e9'; ctx.fillRect(0, iy + 360, SW, 90);
    ctx.fillStyle = '#fcd9a0'; ctx.fillRect(0, iy + 440, SW, 200);
    ctx.strokeStyle = '#7c4a21'; ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(130, iy + 560); ctx.quadraticCurveTo(150, iy + 320, 210, iy + 180); ctx.stroke();
    ctx.strokeStyle = '#16a34a'; ctx.lineWidth = 20;
    for (const [dx, dy] of [[-150, 30], [-110, -70], [0, -110], [120, -60], [150, 40]]) { ctx.beginPath(); ctx.moveTo(210, iy + 180); ctx.quadraticCurveTo(210 + dx * 0.6, iy + 150 + dy, 210 + dx, iy + 190 + dy + Math.sin(t * 2 + dx) * 6); ctx.stroke(); }
    figure({ px: 430, py: iy + 560, h: 400, look: 'shades', seed: 3 }, { cur: { emo: 'laugh', pose: 'cheer', at: 0 }, prev: { pose: 'cheer' }, k: 1, talk: false }, t);
    ctx.fillStyle = '#f97316'; rr(447, iy + 96, 30, 46, 6); ctx.fill(); ctx.fillStyle = '#fff'; rr(447, iy + 90, 30, 12, 5); ctx.fill();
    ctx.restore();
    const hy = iy + ih + 60, likes = Math.floor(d.likes * (0.82 + 0.18 * ease(lt / 3)));
    ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.moveTo(60, hy + 16); ctx.bezierCurveTo(10, hy - 20, 30, hy - 50, 60, hy - 22); ctx.bezierCurveTo(90, hy - 50, 110, hy - 20, 60, hy + 16); ctx.fill();
    font(30, 800); text(likes.toLocaleString('en-GB') + ' likes', 110, hy + 6, INK);
    font(30, 800); text(d.user, 34, hy + 70, INK); const uw = ctx.measureText(d.user + ' ').width;
    font(30, 600); let x = 34 + uw;
    for (const w of d.captionWords || plain(d.caption || '')) { const ww = ctx.measureText(w.t + ' ').width; text(w.t, x, hy + 70, w.t.startsWith('#') ? '#2563eb' : INK); x += ww; }
    font(24, 600); text('2 hours ago', 34, hy + 116, '#94a3b8');
  }

  function appPortfolio(d, lt, t) {
    ctx.fillStyle = '#0b0f14'; ctx.fillRect(0, 0, SW, SH); statusBar('#fff', d.time || '09:12');
    const k = d.dur ? ease((lt - d.at) / d.dur) : 1, v = lerp(d.from, d.to, k), pct = ((v - d.base) / d.base) * 100, up = v >= d.base;
    const col = up ? '#22c55e' : '#ef4444';
    font(28, 700); text('My portfolio', 40, 130, '#94a3b8');
    font(96, 900); text(money(v), 40, 240, '#fff');
    ctx.fillStyle = up ? 'rgba(34,197,94,.18)' : 'rgba(239,68,68,.2)'; rr(40, 270, 400, 64, 32); ctx.fill();
    font(32, 800); text(`${up ? '▲' : '▼'} ${money(Math.abs(v - d.base))} (${Math.abs(pct).toFixed(1)}%)`, 62, 314, col);
    // chart
    const cx0 = 30, cw = SW - 60, cy0 = 390, ch = 360, N = 70, crash = d.trend === 'crash';
    ctx.strokeStyle = 'rgba(255,255,255,.07)'; ctx.lineWidth = 2; for (let i = 0; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(cx0, cy0 + (i * ch) / 4); ctx.lineTo(cx0 + cw, cy0 + (i * ch) / 4); ctx.stroke(); }
    const pts = []; const shown = d.dur ? Math.max(2, Math.floor(N * (0.45 + 0.55 * k))) : N;
    for (let i = 0; i < N; i++) {
      const p = i / (N - 1), bend = crash ? Math.pow(p, 2.2) : Math.pow(p, 1.6);
      const y = crash ? lerp(0.12, 0.9, bend) : lerp(0.86, 0.1, bend);
      pts.push([cx0 + p * cw, cy0 + (y + (hash(i * 3.1 + (crash ? 1 : 7)) - 0.5) * 0.11 * (1 - 0.5 * p)) * ch]);
    }
    ctx.beginPath(); pts.slice(0, shown).forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.strokeStyle = col; ctx.lineWidth = 7; ctx.lineJoin = 'round'; ctx.stroke();
    const [lx, ly] = pts[shown - 1];
    ctx.lineTo(lx, cy0 + ch); ctx.lineTo(cx0, cy0 + ch); ctx.closePath();
    const fg = ctx.createLinearGradient(0, cy0, 0, cy0 + ch); fg.addColorStop(0, up ? 'rgba(34,197,94,.35)' : 'rgba(239,68,68,.35)'); fg.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = fg; ctx.fill();
    circ(lx, ly, 12 + Math.sin(t * 8) * 3, 0, col);
    // holdings
    [['Global Index Fund', 0.7], ['Tech Growth Fund', 1.45]].forEach(([n, m], i) => {
      const y = 790 + i * 100; ctx.fillStyle = '#141b24'; rr(30, y, SW - 60, 84, 22); ctx.fill();
      font(28, 700); text(n, 58, y + 52, '#e2e8f0'); font(28, 800); text(`${pct * m >= 0 ? '+' : '−'}${Math.abs(pct * m).toFixed(1)}%`, SW - 58, y + 52, col, 'right');
    });
    const pulse = d.sell && lt > d.sell.at ? 1 + 0.04 * Math.sin(t * 12) : 1;
    ctx.strokeStyle = '#22c55e'; ctx.lineWidth = 5; rr(30, 1000, SW / 2 - 45, 84, 42); ctx.stroke(); font(34, 900); text('BUY', 30 + (SW / 2 - 45) / 2, 1054, '#22c55e', 'center');
    ctx.save(); ctx.translate(SW * 0.75, 1042); ctx.scale(pulse, pulse); ctx.fillStyle = '#ef4444'; rr(-(SW / 2 - 45) / 2, -42, SW / 2 - 45, 84, 42); ctx.fill(); text('SELL', 0, 12, '#fff', 'center'); ctx.restore();
  }

  function appLock(d, lt) {
    const g = ctx.createLinearGradient(0, 0, SW, SH); g.addColorStop(0, '#312e81'); g.addColorStop(1, '#0f766e'); ctx.fillStyle = g; ctx.fillRect(0, 0, SW, SH);
    statusBar('#fff', d.time || '12:04');
    font(150, 800); text(d.time || '12:04', SW / 2, 290, '#fff', 'center'); font(32, 600); text(d.date || 'Tuesday 14 May', SW / 2, 345, 'rgba(255,255,255,.8)', 'center');
    let y = 430;
    for (const n of d.notifs || []) {
      font(37, 600); const lines = wrap(plain(n.body), SW - 110), bh = 150 + lines.length * 50;
      if (lt >= n.at) {
        const s = backOut((lt - n.at) / 0.4);
        ctx.save(); ctx.translate(SW / 2, y - (1 - s) * 200); ctx.globalAlpha = clamp((lt - n.at) / 0.15);
        ctx.fillStyle = 'rgba(255,255,255,.95)'; rr(-SW / 2 + 24, 0, SW - 48, bh, 38); ctx.fill();
        ctx.fillStyle = n.col || '#2563eb'; rr(-SW / 2 + 48, 24, 52, 52, 14); ctx.fill(); font(30, 900); text('@', -SW / 2 + 74, 61, '#fff', 'center');
        font(24, 700); text((n.app || 'MAIL').toUpperCase(), -SW / 2 + 116, 58, '#64748b'); text('now', SW / 2 - 52, 58, '#94a3b8', 'right');
        font(38, 800); text(n.from, -SW / 2 + 48, 124, INK);
        font(37, 600); lines.forEach((l, i) => text(l.ws.map((w) => w.t).join(' '), -SW / 2 + 48, 180 + i * 50, '#334155'));
        ctx.restore(); ctx.globalAlpha = 1;
      }
      y += bh + 20;
    }
  }

  // ───────────────────────── overlays ─────────────────────────
  function camera(beat, t) {
    let s = 1, ox = 0, oy = 0;
    if (beat) {
      const bt = t - beat.start, bd = beat.end - beat.start;
      if (beat.fx === 'boom') { const d = Math.exp(-bt * 6); ox = Math.sin(t * 90) * 28 * d; oy = Math.cos(t * 77) * 28 * d; s = 1 + 0.17 * easeOut(bt / 0.1) + 0.03 * (bt / bd); }
      if (beat.fx === 'zoom') s = 1 + 0.16 * ease(bt / bd);
      if (beat.fx === 'shake') { ox = Math.sin(t * 80) * 9; oy = Math.cos(t * 63) * 9; s = 1.05; }
    }
    ox += Math.sin(t * 0.7) * 7; oy += Math.sin(t * 0.93 + 1) * 6; s *= 1.025;
    return { s, ox, oy };
  }

  function impact(beat, t) {
    if (!beat || beat.fx !== 'boom') return;
    const bt = t - beat.start, a = Math.exp(-bt * 5);
    if (a < 0.03) return;
    ctx.fillStyle = `rgba(255,255,255,${0.55 * Math.exp(-bt * 16)})`; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = `rgba(21,21,21,${0.75 * a})`;
    const cx = W / 2, cy = 700, fr = Math.floor(t * 15);
    for (let i = 0; i < 34; i++) {
      const an = (i / 34) * Math.PI * 2 + hash(i + fr) * 0.12, r1 = 640 + hash(i * 7 + fr) * 260, hw = 0.012 + hash(i * 3) * 0.014;
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(an) * r1, cy + Math.sin(an) * r1 * 1.25);
      ctx.lineTo(cx + Math.cos(an - hw) * 2200, cy + Math.sin(an - hw) * 2200); ctx.lineTo(cx + Math.cos(an + hw) * 2200, cy + Math.sin(an + hw) * 2200); ctx.fill();
    }
  }

  function banner(t) {
    const TL = window.TL; font(46, 900);
    const lines = wrap(TL.meta.pov, 860), lh = 60, bw = Math.max(...lines.map((l) => l.w)) + 72, bh = lines.length * lh + 44;
    const s = backOut(t / 0.3);
    ctx.save(); ctx.translate(W / 2, 170 + bh / 2); ctx.scale(s, s); ctx.rotate(-0.012);
    ctx.fillStyle = YEL; rr(-bw / 2 + 10, -bh / 2 + 12, bw, bh, 26); ctx.fill();
    ctx.fillStyle = '#111'; rr(-bw / 2, -bh / 2, bw, bh, 26); ctx.fill();
    lines.forEach((ln, li) => { let x = -ln.w / 2; const y = -bh / 2 + 22 + lh * (li + 0.5); ln.ws.forEach((w) => { text(w.t, x, y, w.hl || w.i === 0 ? YEL : '#fff', 'left', 'middle'); x += w.ww + ln.sp; }); });
    ctx.restore();
  }

  function caption(beat, t, cy) {
    if (!beat || !beat.words) return;
    const think = beat.who === 'think', px = think ? 60 : 68, lh = think ? 78 : 88;
    font(px, 900, think);
    const lines = wrap(beat.words, 930);
    let y = cy - ((lines.length - 1) * lh) / 2;
    // speaker tag
    const ts = backOut((t - beat.start) / 0.18);
    ctx.save(); ctx.translate(W / 2, y - lh / 2 - 44); ctx.scale(ts, ts); font(30, 900);
    const tw = ctx.measureText(beat.tag).width + 44;
    ctx.fillStyle = '#111'; rr(-tw / 2 + 4, -24 + 5, tw, 52, 26); ctx.fill();
    ctx.fillStyle = beat.col; rr(-tw / 2, -24, tw, 52, 26); ctx.fill();
    text(beat.tag, 0, 3, '#fff', 'center', 'middle'); ctx.restore();
    font(px, 900, think);
    for (const ln of lines) {
      let x = W / 2 - ln.w / 2;
      for (const w of ln.ws) {
        const a = (t - beat.wt[w.i]) / 0.1;
        if (a > 0) {
          const s = 1 + 0.4 * (1 - easeOut(a));
          ctx.save(); ctx.translate(x + w.ww / 2, y); ctx.scale(s, s); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.lineJoin = 'round'; ctx.lineWidth = 16; ctx.strokeStyle = '#111'; ctx.strokeText(w.t, 0, 0);
          ctx.fillStyle = w.hl ? YEL : think ? '#dbeafe' : '#fff'; ctx.fillText(w.t, 0, 0); ctx.restore();
        }
        x += w.ww + ln.sp;
      }
      y += lh;
    }
  }

  function drawCard(shot, lt) {
    ctx.fillStyle = '#0c0c0e'; ctx.fillRect(0, 0, W, H);
    const s = lerp(1.25, 1, easeOut(lt / 0.25)) + lt * 0.015;
    font(112, 900); const lines = wrap(shot.words, 940);
    ctx.save(); ctx.translate(W / 2, 900); ctx.scale(s, s); ctx.globalAlpha = clamp(lt / 0.12);
    lines.forEach((ln, i) => text(ln.ws.map((w) => w.t).join(' '), 0, (i - (lines.length - 1) / 2) * 128, '#fff', 'center', 'middle'));
    const by = (lines.length * 128) / 2 + 30;
    ctx.fillStyle = YEL; rr(-90 * easeOut(lt / 0.4), by, 180 * easeOut(lt / 0.4), 12, 6); ctx.fill();
    if (shot.sub) { ctx.globalAlpha = clamp((lt - 0.45) / 0.3); font(46, 700); wrap(plain(shot.sub), 860).forEach((ln, i) => text(ln.ws.map((w) => w.t).join(' '), 0, by + 100 + i * 64, '#d4d4d8', 'center', 'middle')); }
    ctx.restore(); ctx.globalAlpha = 1;
  }

  function drawEnd(shot, lt, t) {
    ctx.fillStyle = '#0c0c0e'; ctx.fillRect(0, 0, W, H);
    font(40, 900); const lw = ctx.measureText('THE LESSON').width + 60;
    ctx.fillStyle = YEL; rr(W / 2 - lw / 2, 470, lw, 72, 36); ctx.fill(); text('THE LESSON', W / 2, 508, '#111', 'center', 'middle');
    font(80, 900); const lines = wrap(shot.words, 920);
    let y = 660;
    for (const ln of lines) {
      let x = W / 2 - ln.w / 2;
      for (const w of ln.ws) {
        const a = (lt - shot.wt[w.i]) / 0.12;
        if (a > 0) { const s = 1 + 0.35 * (1 - easeOut(a)); ctx.save(); ctx.translate(x + w.ww / 2, y); ctx.scale(s, s); text(w.t, 0, 0, w.hl ? YEL : '#fff', 'center', 'middle'); ctx.restore(); }
        x += w.ww + ln.sp;
      }
      y += 104;
    }
    const ck = lt - shot.ctaAt;
    if (ck > 0) {
      const s = backOut(ck / 0.3) * (1 + 0.03 * Math.sin(t * 6));
      const keep = [INK, SKIN]; INK = '#fff'; SKIN = '#0c0c0e';
      figure({ px: W / 2, py: y + 380, h: 300, seed: 2 }, { cur: { emo: 'happy', pose: 'wave', at: 0 }, prev: { pose: 'wave' }, k: 1, talk: false }, t);
      [INK, SKIN] = keep;
      ctx.save(); ctx.translate(W / 2, y + 470); ctx.scale(s, s); font(50, 900);
      const cw = ctx.measureText(shot.cta).width + 150;
      ctx.fillStyle = '#fff'; rr(-cw / 2, -52, cw, 104, 52); ctx.fill(); text(shot.cta + '  →', 0, 4, '#111', 'center', 'middle'); ctx.restore();
    }
    ctx.globalAlpha = clamp((lt - 0.4) / 0.4); font(28, 600);
    wrap(plain(window.TL.meta.disclaimer), 880).forEach((ln, i) => text(ln.ws.map((w) => w.t).join(' '), W / 2, 1730 + i * 40, '#8b8b93', 'center', 'middle'));
    ctx.globalAlpha = 1;
  }

  let grainPat = null;
  function grain() {
    if (!grainPat) {
      const g = document.createElement('canvas'); g.width = g.height = 256; const x = g.getContext('2d'), im = x.createImageData(256, 256);
      for (let i = 0; i < 256 * 256; i++) { const v = hash(i * 1.37) * 255; im.data[i * 4] = im.data[i * 4 + 1] = im.data[i * 4 + 2] = v; im.data[i * 4 + 3] = 20; }
      x.putImageData(im, 0, 0); grainPat = ctx.createPattern(g, 'repeat');
    }
    ctx.fillStyle = grainPat; ctx.fillRect(0, 0, W, H);
    const v = ctx.createRadialGradient(W / 2, H / 2, 700, W / 2, H / 2, 1250); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.28)');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  }

  window.drawFrame = function (t) {
    const TL = window.TL;
    boil = Math.floor(t * 10); strokeN = 0;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
    const shot = TL.shots.find((s) => t >= s.start && t < s.end) || TL.shots.at(-1);
    const beat = (shot.beats || []).find((b) => t >= b.start && t < b.end);
    const lt = t - shot.start;
    if (shot.type === 'card') drawCard(shot, lt);
    else if (shot.type === 'end') drawEnd(shot, lt, t);
    else {
      const cam = camera(beat, t), fx = W / 2, fyc = shot.type === 'phone' ? 900 : 560;
      ctx.save(); ctx.translate(fx + cam.ox, fyc + cam.oy); ctx.scale(cam.s, cam.s); ctx.translate(-fx, -fyc);
      if (shot.type === 'scene') {
        background(shot.bg, t);
        for (const [name, def] of Object.entries(shot.actors || {})) figure(def, actorState(shot, name, def, t), t);
        const hs = handState(shot, t); povHands(hs.mode, hs.since, t, shot);
      } else drawPhone(shot, t);
      ctx.restore();
      impact(beat, t);
      banner(t);
      caption(beat, t, shot.type === 'phone' ? 1610 : 1470);
    }
    if (shot.index > 0 && lt < 0.1) { ctx.fillStyle = `rgba(255,255,255,${0.5 * (1 - lt / 0.1)})`; ctx.fillRect(0, 0, W, H); }
    grain();
    ctx.fillStyle = 'rgba(255,255,255,.25)'; ctx.fillRect(0, 0, W, 10); ctx.fillStyle = YEL; ctx.fillRect(0, 0, W * (t / TL.duration), 10);
  };
})();
