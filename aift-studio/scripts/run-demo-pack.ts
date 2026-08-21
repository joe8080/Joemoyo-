/**
 * Produces a complete content pack from the fixture topic and prints what
 * happened. This is the "does the whole thing work" command.
 *
 *   npm run pack:demo                 # text pack + rendered MP4s
 *   npm run pack:demo -- --no-video   # text pack only (fast)
 *   npm run pack:demo -- --only=short
 */
import { bootstrap } from '@/lib/bootstrap';
import { WorkflowEngine } from '@/lib/workflow/engine';
import { DEFAULT_BRAND_SETTINGS } from '@/lib/db/defaults';
import { FIXTURE_TOPIC } from '@/lib/fixtures/northwind';
import { stableId } from '@/lib/util/hash';

const args = process.argv.slice(2);
const withVideo = !args.includes('--no-video');
const only = args.find((a) => a.startsWith('--only='))?.split('=')[1];
const fpsArg = args.find((a) => a.startsWith('--fps='))?.split('=')[1];

const USER_ID = stableId('aift_user', 'owner');

async function main(): Promise<void> {
  const brand = { ...DEFAULT_BRAND_SETTINGS, user_id: USER_ID };
  const { repo, providers, registry, mode } = await bootstrap({ brand });
  await repo.updateBrandSettings(USER_ID, brand);

  const t0 = Date.now();
  const engine = new WorkflowEngine({
    repo, providers, registry,
    log: (level, stage, msg) => {
      const tag = level === 'error' ? 'ERR ' : level === 'warn' ? 'WARN' : 'ok  ';
      console.log(`  ${tag} [${stage}] ${msg}`);
    },
  });

  console.log('\n── Provider mode ' + '─'.repeat(50));
  console.table(mode);

  console.log('\n── Research ' + '─'.repeat(55));
  const research = await engine.intake({
    userId: USER_ID, topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
    jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
  });
  const { claims } = await engine.runResearch(research.id, brand);

  const formats = (only ? [only] : ['deep_dive', 'short']) as Array<'deep_dive' | 'short'>;
  const results: Array<{ format: string; status: string; runtime: string; assets: number; blocking: number }> = [];

  for (const format of formats) {
    console.log(`\n── Production: ${format} ` + '─'.repeat(48 - format.length));
    const job = await engine.createContentJob({
      userId: USER_ID, researchJobId: research.id, format,
      workingTitle: FIXTURE_TOPIC.topic,
    });
    const { job: done, assets } = await engine.produce(job.id, brand, {
      renderVideo: withVideo,
      ...(fpsArg ? { fps: Number(fpsArg) } : {}),
    });
    const checks = await repo.listQualityChecks(job.id);
    const blocking = checks.filter((c) => c.result === 'fail' && c.severity === 'blocking');
    results.push({
      format,
      status: done.status,
      runtime: `${((done.scene_plan?.total_ms ?? 0) / 1000 / 60).toFixed(2)} min`,
      assets: assets.length,
      blocking: blocking.length,
    });
    if (blocking.length > 0) {
      console.log('\n  Blocking failures:');
      for (const b of blocking) console.log(`   ✗ ${b.gate}/${b.check_name}: ${b.details.message}`);
    }
  }

  console.log('\n── Result ' + '─'.repeat(57));
  console.table(results);
  console.log(`\n  ${claims.length} claims in the ledger · artifacts under .artifacts/`);
  console.log(`  elapsed ${((Date.now() - t0) / 1000).toFixed(1)}s\n`);
  console.log('  Nothing was uploaded, scheduled or published. That capability does not exist in this build.\n');
}

main().catch((err: unknown) => {
  console.error('\nDemo pack failed:', err instanceof Error ? err.stack : err);
  process.exitCode = 1;
});
