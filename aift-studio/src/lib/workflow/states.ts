/**
 * The content-job finite state machine.
 *
 * There is no transition into a "published" or "uploading" state because no
 * such state exists. `archived` is terminal and means "package complete, stored
 * for the owner to upload by hand".
 */

export const CONTENT_STATES = [
  'queued',
  'researching',
  'evidence_ready',
  'drafting',
  'visual_planning',
  'rendering',
  'qa_running',
  'needs_review',
  'rework_required',
  'approved_for_archive',
  'archived',
  'blocked',
] as const;

export type ContentState = (typeof CONTENT_STATES)[number];

/** States before human review, from which a job may be sent to `blocked`. */
export const PRE_REVIEW_STATES: readonly ContentState[] = [
  'queued',
  'researching',
  'evidence_ready',
  'drafting',
  'visual_planning',
  'rendering',
  'qa_running',
];

export const TERMINAL_STATES: readonly ContentState[] = ['archived'];

const FORWARD: Record<ContentState, readonly ContentState[]> = {
  queued: ['researching'],
  researching: ['evidence_ready'],
  evidence_ready: ['drafting'],
  drafting: ['visual_planning'],
  visual_planning: ['rendering'],
  rendering: ['qa_running'],
  qa_running: ['needs_review'],
  needs_review: ['approved_for_archive', 'rework_required'],
  rework_required: ['drafting'],
  approved_for_archive: ['archived'],
  archived: [],
  blocked: ['drafting'],
};

/**
 * Transitions that require an authenticated human decision. The workflow engine
 * cannot perform these; only a reviewer action route can.
 */
export const HUMAN_ONLY_TRANSITIONS: ReadonlySet<string> = new Set([
  'needs_review->approved_for_archive',
  'needs_review->rework_required',
  'approved_for_archive->archived',
  'blocked->drafting',
]);

export type TransitionActor = 'workflow' | 'reviewer';

export type TransitionResult =
  | { ok: true }
  | { ok: false; reason: string };

export function transitionKey(from: ContentState, to: ContentState): string {
  return `${from}->${to}`;
}

export function isHumanOnly(from: ContentState, to: ContentState): boolean {
  return HUMAN_ONLY_TRANSITIONS.has(transitionKey(from, to));
}

/**
 * Single source of truth for legality of a state change. The Postgres function
 * `aift_assert_transition` mirrors this table exactly; `tests/workflow/fsm.test.ts`
 * asserts the two never drift.
 */
export function canTransition(
  from: ContentState,
  to: ContentState,
  actor: TransitionActor,
): TransitionResult {
  if (from === to) return { ok: false, reason: `already in state "${from}"` };
  if (TERMINAL_STATES.includes(from)) {
    return { ok: false, reason: `"${from}" is terminal; no further transitions are permitted` };
  }

  const allowedForward = FORWARD[from] ?? [];
  const canBlock = PRE_REVIEW_STATES.includes(from) && to === 'blocked';

  if (!allowedForward.includes(to) && !canBlock) {
    return {
      ok: false,
      reason: `illegal transition ${transitionKey(from, to)}; permitted from "${from}": ${
        [...allowedForward, ...(PRE_REVIEW_STATES.includes(from) ? ['blocked'] : [])].join(', ') || '(none)'
      }`,
    };
  }

  if (isHumanOnly(from, to) && actor !== 'reviewer') {
    return {
      ok: false,
      reason: `${transitionKey(from, to)} requires an authenticated reviewer; the workflow engine may not perform it`,
    };
  }

  return { ok: true };
}

/** Every legal edge, for tests and for the docs generator. */
export function allTransitions(): Array<{ from: ContentState; to: ContentState; humanOnly: boolean }> {
  const edges: Array<{ from: ContentState; to: ContentState; humanOnly: boolean }> = [];
  for (const from of CONTENT_STATES) {
    for (const to of FORWARD[from] ?? []) {
      edges.push({ from, to, humanOnly: isHumanOnly(from, to) });
    }
    if (PRE_REVIEW_STATES.includes(from)) {
      edges.push({ from, to: 'blocked', humanOnly: false });
    }
  }
  return edges;
}

/** Progress fraction used by the dashboard ring. Blocked/rework read as stalled. */
export function stateProgress(state: ContentState): number {
  const order: ContentState[] = [
    'queued', 'researching', 'evidence_ready', 'drafting',
    'visual_planning', 'rendering', 'qa_running', 'needs_review',
    'approved_for_archive', 'archived',
  ];
  const i = order.indexOf(state);
  if (i >= 0) return Math.round((i / (order.length - 1)) * 100);
  return state === 'rework_required' ? 35 : 0;
}
