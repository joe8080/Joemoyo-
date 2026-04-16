# Source Code Research Engine

Dedicated research tool for THE SOURCE CODE book. Takes a topic, searches for scholarly sources, and outputs a structured research brief with verified claims and citations.

## Instructions

The user will provide a research topic or question.

Example: `/source-code-research-engine The psychological impact of music on memory formation`

### Step 1 — Parse the topic
Identify:
- Core subject
- Relevant disciplines (neuroscience, psychology, musicology, sociology, history, economics, etc.)
- Key search terms and academic synonyms

### Step 2 — Research
Search for:
1. Academic papers and studies (Google Scholar, PubMed, JSTOR references)
2. Books and established texts in the field
3. Credible journalism (Guardian, BBC, academic institution press releases)
4. Contradicting or nuancing perspectives

Search queries to use:
- `"[topic]" research study findings`
- `"[topic]" academic paper site:scholar.google.com`
- `"[topic]" peer reviewed journal`
- `[topic] neuroscience/psychology/sociology`

### Step 3 — Output the research brief

```
SOURCE CODE RESEARCH BRIEF
══════════════════════════════════════════════════════════
Topic: [Topic]
Disciplines: [List]
Date: [today's date]

  CORE FINDINGS
  ─────────────────────────────────────────────────────
  [3–5 bullet points of the most important verified findings]
  • [Finding 1] — Source: [Author, Year, Publication]
  • [Finding 2] — Source: [Author, Year, Publication]
  ...

  KEY STUDIES / SOURCES
  ─────────────────────────────────────────────────────
  1. [Study/Book title]
     Author(s): [Names] | Year: [Year] | Publication: [Journal/Publisher]
     Summary: [2–3 sentences]
     Key stat or quote: "[quote or data point]"
     Reliability: ✅ Peer-reviewed / ⚠️ Journalism / 📚 Book

  2. [Study/Book title]
     ...

  NUANCE / COUNTER-ARGUMENTS
  ─────────────────────────────────────────────────────
  • [Counter-point or limitation] — Source: [Reference]

  ANGLES FOR THE BOOK
  ─────────────────────────────────────────────────────
  [3 concrete ways this research could be used in THE SOURCE CODE]
  1. Chapter angle: [Suggestion]
  2. Story hook: [Suggestion]
  3. Practical application: [Suggestion]

  FOLLOW-UP QUESTIONS
  ─────────────────────────────────────────────────────
  [2–3 questions this research raises that could be worth investigating further]

  CITATIONS (formatted for reference list)
  ─────────────────────────────────────────────────────
  [Author Surname, Initial. (Year). Title. Journal/Publisher. DOI/URL if available]
```

### Quality Standards
- Only cite sources that can be verified (no hallucinated studies)
- If a specific paper cannot be confirmed, note it as "needs verification"
- Distinguish peer-reviewed from journalistic sources
- Flag if a finding is contested or has been superseded
