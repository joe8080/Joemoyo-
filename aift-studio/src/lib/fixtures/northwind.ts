import type { ClaimType, SourceTier } from '@/lib/schemas/content';

/**
 * SYNTHETIC RESEARCH CORPUS — "Northwind Semiconductor Corporation (NWSC)".
 *
 * Northwind does not exist. Every figure below is invented so the pipeline can
 * be exercised, demonstrated and tested end to end without a single real
 * investment datum entering the repository. Source labels rendered on screen
 * say "synthetic fixture" for exactly this reason.
 *
 * Replacing this file with a live ResearchProvider is the only change needed to
 * move from demo to real research.
 */

export type FixtureFact = {
  id: string;
  text: string;
  type: ClaimType;
  excerpt: string;
  asOf: string;
  confidence: number;
  direction: 'bull' | 'bear' | 'neutral';
  uncertainty: string;
};

export type FixtureSource = {
  url: string;
  title: string;
  publisher: string;
  publishedAt: string;
  tier: SourceTier;
  licenceNotes: string;
  fullText: string;
  facts: FixtureFact[];
};

export type FixtureSeries = {
  key: string;
  label: string;
  unit: string;
  sourceLabel: string;
  asOf: string;
  claimIds: string[];
  points: Array<{ x: string; y: number }>;
};

export const REFERENCE_DATE = '2026-08-14';

export const FIXTURE_SOURCES: FixtureSource[] = [
  {
    url: 'fixture://northwind/10q-fy26q3',
    title: 'Northwind Semiconductor Corporation — Form 10-Q, quarter ended 27 June 2026',
    publisher: 'Northwind Semiconductor Corporation (synthetic filing)',
    publishedAt: '2026-07-30',
    tier: 'primary_filing',
    licenceNotes: 'Synthetic fixture authored for this repository. Not a real filing.',
    fullText: [
      'Item 2. Management’s Discussion and Analysis.',
      'Revenue for the third quarter of fiscal 2026 was $4.61 billion, compared with $2.88 billion in the third quarter of fiscal 2025.',
      'Data Center segment revenue was $3.24 billion, or 70.3% of total revenue, compared with 48.6% in the prior-year quarter.',
      'Gross margin was 58.4%, compared with 54.1% in the prior-year quarter. The improvement reflects a richer product mix, partially offset by higher advanced-packaging costs.',
      'Purchase commitments and capacity prepayments totalled $6.10 billion as of 27 June 2026, compared with $2.75 billion as of 28 June 2025.',
      'Two customers individually accounted for more than 10% of revenue in the quarter, representing 31% and 14% of revenue respectively.',
      'Item 1A. Risk Factors. We depend on a limited number of third-party foundries and on a single supplier for advanced packaging capacity. Any disruption at these suppliers would materially affect our ability to meet demand.',
    ].join('\n\n'),
    facts: [
      {
        id: 'F-REV', type: 'financial_statement', direction: 'bull', confidence: 0.95, asOf: '2026-06-27',
        text: 'Northwind reported third-quarter fiscal 2026 revenue of $4.61 billion, up from $2.88 billion a year earlier.',
        excerpt: 'Revenue for the third quarter of fiscal 2026 was $4.61 billion, compared with $2.88 billion in the third quarter of fiscal 2025.',
        uncertainty: 'A single quarter of reported revenue, not a trend and not a forecast.',
      },
      {
        id: 'F-MIX', type: 'financial_statement', direction: 'neutral', confidence: 0.93, asOf: '2026-06-27',
        text: 'Data Center accounted for 70.3% of Northwind revenue in the quarter, against 48.6% a year earlier.',
        excerpt: 'Data Center segment revenue was $3.24 billion, or 70.3% of total revenue, compared with 48.6% in the prior-year quarter.',
        uncertainty: 'Segment concentration cuts both ways: it is the growth engine and the single largest exposure.',
      },
      {
        id: 'F-GM', type: 'financial_statement', direction: 'bull', confidence: 0.92, asOf: '2026-06-27',
        text: 'Reported gross margin was 58.4%, against 54.1% in the prior-year quarter.',
        excerpt: 'Gross margin was 58.4%, compared with 54.1% in the prior-year quarter. The improvement reflects a richer product mix, partially offset by higher advanced-packaging costs.',
        uncertainty: 'The filing attributes the move to mix, which can reverse as readily as it arrived.',
      },
      {
        id: 'F-COMMIT', type: 'financial_statement', direction: 'neutral', confidence: 0.9, asOf: '2026-06-27',
        text: 'Purchase commitments and capacity prepayments stood at $6.10 billion, against $2.75 billion a year earlier.',
        excerpt: 'Purchase commitments and capacity prepayments totalled $6.10 billion as of 27 June 2026, compared with $2.75 billion as of 28 June 2025.',
        uncertainty: 'Commitments are a signal of expected demand and a fixed obligation if that demand softens.',
      },
      {
        id: 'F-CONC', type: 'insider_or_ownership', direction: 'bear', confidence: 0.94, asOf: '2026-06-27',
        text: 'Two customers each represented more than 10% of revenue, at 31% and 14%.',
        excerpt: 'Two customers individually accounted for more than 10% of revenue in the quarter, representing 31% and 14% of revenue respectively.',
        uncertainty: 'Customer concentration is disclosed as a fact; its consequences depend on contracts the filing does not publish.',
      },
      {
        id: 'F-SUPPLY', type: 'causal', direction: 'bear', confidence: 0.88, asOf: '2026-06-27',
        text: 'The company states that it relies on a limited number of foundries and a single advanced-packaging supplier.',
        excerpt: 'We depend on a limited number of third-party foundries and on a single supplier for advanced packaging capacity. Any disruption at these suppliers would materially affect our ability to meet demand.',
        uncertainty: 'This is the company’s own risk language, not an independent assessment of failure probability.',
      },
    ],
  },
  {
    url: 'fixture://northwind/q3-earnings-call',
    title: 'Northwind Semiconductor — Q3 FY2026 earnings call transcript',
    publisher: 'Northwind Semiconductor Investor Relations (synthetic)',
    publishedAt: '2026-07-30',
    tier: 'primary_company',
    licenceNotes: 'Synthetic fixture. Not a real transcript.',
    fullText: [
      'CFO: For the fourth quarter we are guiding to revenue of $5.05 billion, plus or minus 2 percent.',
      'CFO: We expect gross margin of approximately 57.5 percent, reflecting a full quarter of the higher packaging cost we flagged last quarter.',
      'CEO: Demand visibility now extends roughly four quarters, versus about two a year ago. That is a statement about orders, not a promise about the cycle.',
      'Analyst: How much of the backlog is cancellable? CFO: A meaningful portion carries cancellation terms. We do not disclose the split.',
    ].join('\n\n'),
    facts: [
      {
        id: 'F-GUIDE', type: 'forecast_or_guidance', direction: 'bull', confidence: 0.85, asOf: '2026-07-30',
        text: 'Management guided fourth-quarter revenue to approximately $5.05 billion, plus or minus two per cent.',
        excerpt: 'For the fourth quarter we are guiding to revenue of $5.05 billion, plus or minus 2 percent.',
        uncertainty: 'Guidance is a company estimate. It is not a result and it is routinely revised.',
      },
      {
        id: 'F-GMGUIDE', type: 'forecast_or_guidance', direction: 'bear', confidence: 0.83, asOf: '2026-07-30',
        text: 'Management guided fourth-quarter gross margin to approximately 57.5%, below the 58.4% just reported.',
        excerpt: 'We expect gross margin of approximately 57.5 percent, reflecting a full quarter of the higher packaging cost we flagged last quarter.',
        uncertainty: 'A guided step down of under a point; small enough to be noise, disclosed enough to be worth naming.',
      },
      {
        id: 'F-VIS', type: 'contextual', direction: 'neutral', confidence: 0.75, asOf: '2026-07-30',
        text: 'The company says order visibility now extends about four quarters, against roughly two a year ago.',
        excerpt: 'Demand visibility now extends roughly four quarters, versus about two a year ago. That is a statement about orders, not a promise about the cycle.',
        uncertainty: 'Visibility is management’s characterisation of its own order book.',
      },
      {
        id: 'F-CANCEL', type: 'contextual', direction: 'bear', confidence: 0.8, asOf: '2026-07-30',
        text: 'Management confirmed that a meaningful portion of backlog is cancellable and declined to disclose the split.',
        excerpt: 'A meaningful portion carries cancellation terms. We do not disclose the split.',
        uncertainty: 'An undisclosed split is an open question, not a hidden negative.',
      },
    ],
  },
  {
    url: 'fixture://industry/packaging-capacity-note',
    title: 'Advanced packaging capacity: 2024–2026 additions and lead times',
    publisher: 'Fixture Industry Research Group (synthetic)',
    publishedAt: '2026-06-18',
    tier: 'specialist',
    licenceNotes: 'Synthetic fixture standing in for a specialist industry note.',
    fullText: [
      'Industry advanced-packaging capacity is estimated to have grown at a 41% compound annual rate between calendar 2024 and 2026.',
      'Average quoted lead times for advanced packaging slots moved from 14 weeks in early 2024 to 31 weeks by mid-2026.',
      'Capacity additions are concentrated: the three largest providers account for an estimated 78% of qualified advanced-packaging output.',
    ].join('\n\n'),
    facts: [
      {
        id: 'F-LEAD', type: 'contextual', direction: 'neutral', confidence: 0.7, asOf: '2026-06-18',
        text: 'Quoted lead times for advanced packaging are estimated to have moved from about 14 weeks in early 2024 to about 31 weeks by mid-2026.',
        excerpt: 'Average quoted lead times for advanced packaging slots moved from 14 weeks in early 2024 to 31 weeks by mid-2026.',
        uncertainty: 'An industry estimate from a single specialist source, not an audited figure.',
      },
      {
        id: 'F-CONCIND', type: 'contextual', direction: 'bear', confidence: 0.68, asOf: '2026-06-18',
        text: 'An estimated 78% of qualified advanced-packaging output sits with three providers.',
        excerpt: 'Capacity additions are concentrated: the three largest providers account for an estimated 78% of qualified advanced-packaging output.',
        uncertainty: 'Estimated share, single source, and definitions of "qualified" vary between analysts.',
      },
    ],
  },
  {
    url: 'fixture://education/concentration-risk-primer',
    title: 'Customer concentration disclosure: what the 10% threshold means',
    publisher: 'Fixture Financial Education Desk (synthetic)',
    publishedAt: '2026-02-04',
    tier: 'specialist',
    licenceNotes: 'Synthetic fixture standing in for an educational reference.',
    fullText: [
      'Registrants disclose customers accounting for 10% or more of consolidated revenue because the loss of such a customer could have a material effect.',
      'Concentration is a disclosure about dependency, not a prediction. A concentrated customer base can be extremely profitable while it lasts.',
    ].join('\n\n'),
    facts: [
      {
        id: 'F-DEF', type: 'definitional', direction: 'neutral', confidence: 0.9, asOf: '2026-02-04',
        text: 'The 10% customer-concentration disclosure exists because losing such a customer could have a material effect on the business.',
        excerpt: 'Registrants disclose customers accounting for 10% or more of consolidated revenue because the loss of such a customer could have a material effect.',
        uncertainty: '',
      },
      {
        id: 'F-DEF2', type: 'definitional', direction: 'neutral', confidence: 0.9, asOf: '2026-02-04',
        text: 'Concentration describes dependency; it does not forecast whether that dependency will be tested.',
        excerpt: 'Concentration is a disclosure about dependency, not a prediction. A concentrated customer base can be extremely profitable while it lasts.',
        uncertainty: '',
      },
    ],
  },
];

/** Structured series for deterministic charts. Never model-generated. */
export const FIXTURE_SERIES: FixtureSeries[] = [
  {
    key: 'revenue_by_quarter',
    label: 'Total revenue',
    unit: '$bn',
    sourceLabel: 'Northwind 10-Q (synthetic fixture)',
    asOf: '2026-06-27',
    claimIds: ['C-001'],
    points: [
      { x: 'FY25 Q3', y: 2.88 }, { x: 'FY25 Q4', y: 3.11 }, { x: 'FY26 Q1', y: 3.54 },
      { x: 'FY26 Q2', y: 4.02 }, { x: 'FY26 Q3', y: 4.61 },
    ],
  },
  {
    key: 'datacenter_share',
    label: 'Data Center share of revenue',
    unit: '%',
    sourceLabel: 'Northwind 10-Q (synthetic fixture)',
    asOf: '2026-06-27',
    claimIds: ['C-002'],
    points: [
      { x: 'FY25 Q3', y: 48.6 }, { x: 'FY25 Q4', y: 53.2 }, { x: 'FY26 Q1', y: 59.8 },
      { x: 'FY26 Q2', y: 65.1 }, { x: 'FY26 Q3', y: 70.3 },
    ],
  },
  {
    key: 'gross_margin',
    label: 'Gross margin',
    unit: '%',
    sourceLabel: 'Northwind 10-Q + Q3 call (synthetic fixture)',
    asOf: '2026-07-30',
    claimIds: ['C-003'],
    points: [
      { x: 'FY25 Q3', y: 54.1 }, { x: 'FY25 Q4', y: 55.0 }, { x: 'FY26 Q1', y: 56.2 },
      { x: 'FY26 Q2', y: 57.3 }, { x: 'FY26 Q3', y: 58.4 }, { x: 'FY26 Q4E', y: 57.5 },
    ],
  },
  {
    key: 'commitments',
    label: 'Purchase commitments & prepayments',
    unit: '$bn',
    sourceLabel: 'Northwind 10-Q (synthetic fixture)',
    asOf: '2026-06-27',
    claimIds: ['C-004'],
    points: [
      { x: 'FY25 Q3', y: 2.75 }, { x: 'FY25 Q4', y: 3.40 }, { x: 'FY26 Q1', y: 4.25 },
      { x: 'FY26 Q2', y: 5.18 }, { x: 'FY26 Q3', y: 6.10 },
    ],
  },
  {
    key: 'packaging_lead_time',
    label: 'Advanced packaging lead time',
    unit: 'weeks',
    sourceLabel: 'Fixture Industry Research Group (synthetic)',
    asOf: '2026-06-18',
    claimIds: ['C-009'],
    points: [
      { x: 'H1 24', y: 14 }, { x: 'H2 24', y: 19 }, { x: 'H1 25', y: 24 },
      { x: 'H2 25', y: 28 }, { x: 'H1 26', y: 31 },
    ],
  },
];

export const FIXTURE_TOPIC = {
  topic: 'Northwind Semiconductor’s data-centre pivot: what the Q3 filing actually shows',
  ticker: 'NWSC',
  referenceDate: REFERENCE_DATE,
};
