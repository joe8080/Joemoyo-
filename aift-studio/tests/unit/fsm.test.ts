import { describe, expect, it } from 'vitest';
import { readFile } from 'node:fs/promises';
import {
  CONTENT_STATES, allTransitions, canTransition, isHumanOnly, stateProgress,
} from '@/lib/workflow/states';

describe('content-job finite state machine', () => {
  it('has no state that means published, uploaded or scheduled', () => {
    for (const s of CONTENT_STATES) {
      expect(s).not.toMatch(/publish|upload|schedul|live|broadcast/iu);
    }
  });

  it('walks the happy path only in order', () => {
    const path = [
      'queued', 'researching', 'evidence_ready', 'drafting',
      'visual_planning', 'rendering', 'qa_running', 'needs_review',
    ] as const;
    for (let i = 0; i < path.length - 1; i += 1) {
      expect(canTransition(path[i]!, path[i + 1]!, 'workflow').ok).toBe(true);
    }
  });

  it('refuses to skip a stage', () => {
    expect(canTransition('queued', 'needs_review', 'workflow').ok).toBe(false);
    expect(canTransition('drafting', 'qa_running', 'workflow').ok).toBe(false);
    expect(canTransition('evidence_ready', 'rendering', 'workflow').ok).toBe(false);
  });

  it('will not let the workflow engine approve or archive its own output', () => {
    const approve = canTransition('needs_review', 'approved_for_archive', 'workflow');
    expect(approve.ok).toBe(false);
    expect(approve.ok === false && approve.reason).toMatch(/reviewer/u);

    expect(canTransition('approved_for_archive', 'archived', 'workflow').ok).toBe(false);
  });

  it('lets an authenticated reviewer approve, then archive — in that order', () => {
    expect(canTransition('needs_review', 'approved_for_archive', 'reviewer').ok).toBe(true);
    expect(canTransition('approved_for_archive', 'archived', 'reviewer').ok).toBe(true);
    // Never straight to archived.
    expect(canTransition('needs_review', 'archived', 'reviewer').ok).toBe(false);
    expect(canTransition('qa_running', 'archived', 'reviewer').ok).toBe(false);
  });

  it('treats archived as terminal', () => {
    for (const s of CONTENT_STATES) {
      expect(canTransition('archived', s, 'reviewer').ok).toBe(false);
    }
  });

  it('allows blocking from any pre-review stage and only unblocking by a human', () => {
    for (const s of ['queued', 'researching', 'evidence_ready', 'drafting', 'visual_planning', 'rendering', 'qa_running'] as const) {
      expect(canTransition(s, 'blocked', 'workflow').ok).toBe(true);
    }
    expect(canTransition('needs_review', 'blocked', 'workflow').ok).toBe(false);
    expect(canTransition('blocked', 'drafting', 'workflow').ok).toBe(false);
    expect(canTransition('blocked', 'drafting', 'reviewer').ok).toBe(true);
  });

  it('supports the rework loop', () => {
    expect(canTransition('needs_review', 'rework_required', 'reviewer').ok).toBe(true);
    expect(canTransition('rework_required', 'drafting', 'workflow').ok).toBe(true);
  });

  it('reports monotonic progress along the happy path', () => {
    expect(stateProgress('queued')).toBeLessThan(stateProgress('drafting'));
    expect(stateProgress('drafting')).toBeLessThan(stateProgress('needs_review'));
    expect(stateProgress('archived')).toBe(100);
  });

  /**
   * The TypeScript table and the Postgres function are two implementations of
   * one rule. This test is what stops them drifting: it reads the migration and
   * checks every edge the engine believes in appears there with the same actor.
   */
  it('matches the transition table enforced in Postgres', async () => {
    const sql = await readFile('supabase/migrations/20260821000100_aift_core.sql', 'utf8');
    const fn = sql.slice(sql.indexOf('function public.aift_transition_allowed'), sql.indexOf('aift_enforce_transition'));

    const humanBlock = fn.slice(fn.indexOf('-- Human-only'), fn.indexOf('-- Workflow'));
    const workflowBlock = fn.slice(fn.indexOf('-- Workflow'), fn.indexOf('-- Any pre-review'));

    for (const edge of allTransitions()) {
      if (edge.to === 'blocked') continue; // covered by the catch-all clause
      const pair = `('${edge.from}','${edge.to}')`;
      const block = edge.humanOnly ? humanBlock : workflowBlock;
      expect(block.replace(/\s+/gu, ''), `${pair} missing from the SQL ${edge.humanOnly ? 'human-only' : 'workflow'} list`)
        .toContain(pair.replace(/\s+/gu, ''));
      expect(isHumanOnly(edge.from, edge.to)).toBe(edge.humanOnly);
    }
  });
});
