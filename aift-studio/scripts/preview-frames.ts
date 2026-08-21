/**
 * Renders one still per composition type so the visual system can be reviewed
 * without waiting for a full encode.
 *
 *   npm run preview -- --format=deep_dive --out=.artifacts/preview
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { bootstrap } from '@/lib/bootstrap';
import { WorkflowEngine } from '@/lib/workflow/engine';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import { FIXTURE_TOPIC } from '@/lib/fixtures/northwind';
import { stableId } from '@/lib/util/hash';
import { renderStill } from '@/lib/video/render';

const args = process.argv.slice(2);
const format = (args.find((a) => a.startsWith('--format='))?.split('=')[1] ?? 'deep_dive') as 'deep_dive' | 'short';
const outDir = args.find((a) => a.startsWith('--out='))?.split('=')[1] ?? join('.artifacts', 'preview', format);
const USER_ID = stableId('aift_user', 'owner');

async function main(): Promise<void> {
  const brand = { ...DEFAULT_BRAND_SETTINGS, user_id: USER_ID };
  const { repo, providers, registry } = await bootstrap({ brand });
  await repo.updateBrandSettings(USER_ID, brand);
  const engine = new WorkflowEngine({ repo, providers, registry });

  const research = await engine.intake({
    userId: USER_ID, topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
    jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
  });
  await engine.runResearch(research.id, brand);
  const job = await engine.createContentJob({
    userId: USER_ID, researchJobId: research.id, format, workingTitle: FIXTURE_TOPIC.topic,
  });
  await engine.produce(job.id, brand, { renderVideo: false });

  const done = (await repo.getContentJob(job.id))!;
  const plan = done.scene_plan!;
  const assets = await repo.listAssets(job.id);
  const htmlAsset = assets.find((a) => a.asset_type === 'composition_html')!;
  const html = new TextDecoder().decode(await providers.storage.get(htmlAsset.storage_key));

  await mkdir(outDir, { recursive: true });
  await writeFile(join(outDir, 'composition.html'), html);

  // One frame per distinct composition, taken 70% through the scene so the
  // entrance animation has resolved and the exit has not begun.
  const seen = new Set<string>();
  const picks = plan.scenes.filter((s) => (seen.has(s.composition) ? false : (seen.add(s.composition), true)));

  for (const scene of picks) {
    const at = scene.start_ms + Math.round(scene.duration_ms * 0.7);
    const out = join(outDir, `${scene.composition}.png`);
    await renderStill({ html, width: plan.width, height: plan.height, atMs: at, outPath: out });
    console.log(`  ${scene.composition.padEnd(18)} → ${out}`);
  }
  console.log(`\n${picks.length} composition(s) rendered for ${format}. HTML at ${join(outDir, 'composition.html')}\n`);
  void readFile;
}

main().catch((e: unknown) => { console.error(e); process.exitCode = 1; });
