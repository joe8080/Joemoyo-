// West Africa base map for OGX code films. Natural Earth 1:10m (public domain) via world-atlas.
// Writes remotion/src/geo.json: SVG paths in a fixed Mercator frame (W x H), plus projected city points.
import fs from 'fs';
import {feature} from 'topojson-client';
import {geoMercator, geoPath, geoBounds} from 'd3-geo';
const load = (r) => { const t = JSON.parse(fs.readFileSync(new URL(`./node_modules/world-atlas/countries-${r}.json`, import.meta.url))); return feature(t, t.objects.countries).features; };
const HI = ['Benin', 'Togo', 'Nigeria', 'Ghana'];
const fc = {features: [...load('50m').filter((f) => !HI.includes(f.properties.name)), ...load('10m').filter((f) => HI.includes(f.properties.name))]};
const W = 4000, H = 2600;
const box = {type: 'Feature', geometry: {type: 'MultiPoint', coordinates: [[-19, -3], [17, 21]]}};
const proj = geoMercator().fitExtent([[0, 0], [W, H]], box);
const path = geoPath(proj).digits(1);
const keep = fc.features.filter((f) => { const [[a, b], [c, d]] = geoBounds(f); return !['France', 'Netherlands'].includes(f.properties.name) && a <= c && c > -22 && a < 19 && d > -5 && b < 23; });
const pts = {cotonou: [2.42, 6.37], ouidah: [2.085, 6.366], portonovo: [2.605, 6.497], abomey: [1.991, 7.182], benincity: [5.627, 6.335], dogba: [2.47, 6.78], lagos: [3.39, 6.45], accra: [-0.19, 5.6]};
const out = {W, H, countries: keep.map((f) => ({name: f.properties.name, d: path(f)})), pts: Object.fromEntries(Object.entries(pts).map(([k, v]) => [k, proj(v).map((n) => +n.toFixed(1))]))};
fs.writeFileSync(new URL('./src/geo.json', import.meta.url), JSON.stringify(out));
console.log(keep.length, 'countries', keep.map((f) => f.properties.name).join(', '));
console.log(out.pts, (JSON.stringify(out).length / 1024).toFixed(0) + ' KB');
