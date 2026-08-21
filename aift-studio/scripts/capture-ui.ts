import { chromium } from 'playwright-core';
import { resolveChromiumPath } from '@/lib/video/chromium';
import { mkdir } from 'node:fs/promises';

const base = process.argv[2] ?? 'http://localhost:3111';
const out = process.argv[3] ?? '.artifacts/ui';
await mkdir(out, { recursive: true });

const browser = await chromium.launch({ executablePath: resolveChromiumPath()! });
const page = await browser.newPage({ viewport: { width: 1500, height: 1150 }, deviceScaleFactor: 1 });
page.setDefaultTimeout(600_000);

await page.goto(`${base}/`, { waitUntil: 'networkidle' });
await page.getByRole('button', { name: /Run the fixture topic/u }).click();
await page.waitForLoadState('networkidle');

await page.goto(`${base}/research`, { waitUntil: 'networkidle' });
console.log('producing the Short with a real render — this takes a few minutes…');
await page.getByRole('button', { name: /Produce Short/u }).first().click();
await page.waitForLoadState('networkidle', { timeout: 900_000 });

// The form response can land before the server action has finished writing, so
// poll the job's own status rather than trusting the navigation.
for (let i = 0; i < 400; i += 1) {
  await page.goto(`${base}/`, { waitUntil: 'networkidle' });
  const text = await page.locator('table').first().innerText().catch(() => '');
  if (!/rendering|qa_running|visual_planning|drafting/u.test(text)) break;
  await page.waitForTimeout(3000);
}
console.log('done');

for (const [name, path] of [
  ['dashboard', '/'], ['research', '/research'], ['studio', '/studio'],
  ['brand', '/brand'], ['log', '/log'], ['security', '/security'],
] as const) {
  await page.goto(`${base}${path}`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${out}/${name}.png` });
  console.log(`  ${name}`);
}

await page.goto(`${base}/review`, { waitUntil: 'networkidle' });
const href = await page.locator('a[href^="/review/"]').first().getAttribute('href');
if (href) {
  await page.goto(`${base}${href}`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${out}/review-room.png` });
  console.log('  review-room');
  const studio = href.replace('/review/', '/studio/');
  await page.goto(`${base}${studio}`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${out}/studio-detail.png` });
  console.log('  studio-detail');
}
await browser.close();
