'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { getBrand, getRuntime, ownerId, requireReviewer } from '@/lib/server/runtime';
import { signOutSession } from '@/lib/server/auth';
import { FIXTURE_TOPIC } from '@/lib/fixtures/northwind';
import { stableId } from '@/lib/util/hash';
import type { BrandSettings } from '@/lib/domain';

/**
 * Every mutation the UI can perform.
 *
 * Note what is not here: nothing publishes, uploads, schedules or transmits a
 * pack anywhere. The furthest a pack can travel is `archived`, and that takes
 * two separate authenticated reviewer decisions.
 */

export async function createResearchJob(form: FormData): Promise<void> {
  const { engine } = await getRuntime();
  const brand = await getBrand();
  const topic = String(form.get('topic') ?? '').trim();
  const ticker = String(form.get('ticker') ?? '').trim() || null;
  const referenceDate = String(form.get('reference_date') ?? '').trim();

  if (!topic) throw new Error('A topic is required.');
  const job = await engine.intake({
    userId: await ownerId(), topic, ticker, jobType: 'deep_dive',
    referenceDate: referenceDate || new Date().toISOString().slice(0, 10),
  });
  await engine.runResearch(job.id, brand);
  revalidatePath('/research');
  revalidatePath('/');
}

export async function seedFixtureTopic(): Promise<void> {
  const { engine } = await getRuntime();
  const brand = await getBrand();
  const job = await engine.intake({
    userId: await ownerId(), topic: FIXTURE_TOPIC.topic, ticker: FIXTURE_TOPIC.ticker,
    jobType: 'deep_dive', referenceDate: FIXTURE_TOPIC.referenceDate,
  });
  await engine.runResearch(job.id, brand);
  revalidatePath('/research');
  revalidatePath('/');
}

export async function produceContent(form: FormData): Promise<void> {
  const { engine } = await getRuntime();
  const brand = await getBrand();
  const researchJobId = String(form.get('research_job_id'));
  const format = String(form.get('format')) as 'deep_dive' | 'short';
  const withVideo = form.get('with_video') === 'on';

  const job = await engine.createContentJob({
    userId: await ownerId(), researchJobId, format,
    workingTitle: (await (await getRuntime()).repo.getResearchJob(researchJobId))?.topic ?? 'Untitled',
  });
  await engine.produce(job.id, brand, { renderVideo: withVideo });
  revalidatePath('/');
  revalidatePath('/studio');
  revalidatePath('/review');
}

export async function approveForArchive(form: FormData): Promise<void> {
  // The engine cannot reach this transition; only an authenticated reviewer can.
  const reviewer = await requireReviewer();
  const { repo } = await getRuntime();
  const id = String(form.get('content_job_id'));
  const feedback = String(form.get('feedback') ?? '');

  await repo.transition(id, 'approved_for_archive', 'reviewer', 'approved by owner');
  await repo.recordReviewEvent({
    id: stableId('aift_review_event', `${id}:approve:${Date.now()}`),
    content_job_id: id, reviewer_id: reviewer, decision: 'approved_for_archive',
    reason_codes: ['owner_approved'], freeform_feedback: feedback,
    created_at: new Date().toISOString(),
  });
  revalidatePath('/review');
  revalidatePath('/');
}

export async function archivePack(form: FormData): Promise<void> {
  const reviewer = await requireReviewer();
  const { repo } = await getRuntime();
  const id = String(form.get('content_job_id'));

  await repo.transition(id, 'archived', 'reviewer', 'archived for manual upload');
  await repo.recordReviewEvent({
    id: stableId('aift_review_event', `${id}:archive:${Date.now()}`),
    content_job_id: id, reviewer_id: reviewer, decision: 'archived',
    reason_codes: ['stored_for_manual_upload'], freeform_feedback: '',
    created_at: new Date().toISOString(),
  });
  revalidatePath('/review');
  revalidatePath('/');
}

export async function requestRework(form: FormData): Promise<void> {
  const reviewer = await requireReviewer();
  const { repo } = await getRuntime();
  const id = String(form.get('content_job_id'));
  const feedback = String(form.get('feedback') ?? '');
  const reasons = String(form.get('reason_codes') ?? '').split(',').map((s) => s.trim()).filter(Boolean);

  const job = await repo.getContentJob(id);
  await repo.transition(id, job?.status === 'blocked' ? 'drafting' : 'rework_required', 'reviewer', 'rework requested');
  await repo.recordReviewEvent({
    id: stableId('aift_review_event', `${id}:rework:${Date.now()}`),
    content_job_id: id, reviewer_id: reviewer,
    decision: job?.status === 'blocked' ? 'unblocked' : 'rework_required',
    reason_codes: reasons.length > 0 ? reasons : ['owner_rework'],
    freeform_feedback: feedback, created_at: new Date().toISOString(),
  });
  revalidatePath('/review');
  revalidatePath('/');
}

export async function saveBrand(form: FormData): Promise<void> {
  const { repo } = await getRuntime();
  const current = await getBrand();

  const patch: Partial<BrandSettings> = {
    channel_name: String(form.get('channel_name') ?? current.channel_name),
    voice_guide: String(form.get('voice_guide') ?? current.voice_guide),
    audience_profile: String(form.get('audience_profile') ?? current.audience_profile),
    disclosure_text: String(form.get('disclosure_text') ?? current.disclosure_text),
    default_video_length_minutes: Number(form.get('default_video_length_minutes') ?? current.default_video_length_minutes),
    shorts_enabled: form.get('shorts_enabled') === 'on',
    approved_source_domains: splitLines(String(form.get('approved_source_domains') ?? '')),
    banned_phrases: splitLines(String(form.get('banned_phrases') ?? '')),
    visual_style: {
      ...current.visual_style,
      background: String(form.get('c_background') ?? current.visual_style.background),
      accent: String(form.get('c_accent') ?? current.visual_style.accent),
      accent_2: String(form.get('c_accent_2') ?? current.visual_style.accent_2),
      ink: String(form.get('c_ink') ?? current.visual_style.ink),
    },
    private_context_allowlist: {
      ...current.private_context_allowlist,
      research_topics: form.get('allow_research_topics') === 'on',
      agent_rules: form.get('allow_agent_rules') === 'on',
      intelligence_flags: form.get('allow_intelligence_flags') === 'on',
      market_snapshots: form.get('allow_market_snapshots') === 'on',
      macro_indicators: form.get('allow_macro_indicators') === 'on',
      portfolio_themes: form.get('allow_portfolio_themes') === 'on',
      // Not settable from the UI, and not settable from anywhere else either.
      portfolio_values: false,
    },
  };

  if (!patch.disclosure_text || patch.disclosure_text.trim().length < 40) {
    throw new Error('The disclosure text is required and must be a complete sentence.');
  }

  await repo.updateBrandSettings(await ownerId(), patch);
  revalidatePath('/brand');
}

export async function signOutAction(): Promise<void> {
  await signOutSession();
  redirect('/login');
}

function splitLines(v: string): string[] {
  return v.split(/[\n,]/u).map((s) => s.trim()).filter(Boolean);
}
