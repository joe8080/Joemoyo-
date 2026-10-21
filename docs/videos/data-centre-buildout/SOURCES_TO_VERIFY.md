# Sources and verification log (21 Oct 2026)

Primary data: Joe's Supabase "finance chief" vault (snapshot 2026-10-09) and the Data Centre Power Map / AI Stack artifacts built from it.
Second check: web search against company results coverage. Script = VOICEOVER.txt (796 words).

## CONFIRMED (vault AND web agree)
- Alphabet 2026 capex guide raised to $195–205B from $180–190B; Q2 capex $44.9B; Cloud backlog $514B.
- Amazon 2026 capex guide ~$220B (from ~$200B); AWS +36.7% to ~$42B; backlog $496B.
- Microsoft CY26 capex ~$175B after lease reclassification, from ~$190B. CFO: underlying plan unchanged. (Film only says "more than $700B" in total, so it holds under either figure.)
- Meta Q2 free cash flow ~$0.8B (sources show $784M).
- Combined 2026 spend is more than $700B: Amazon 220 + Alphabet ~200 + Microsoft ~175 + Meta ~137 = about $730B.
- Big-four Q2 capex growth +79%: $170.5B vs $95.0B (checked by arithmetic from the four reported quarters).

## CORRECTED in the script after checking
1. "Close to double last year" -> "up around eighty percent". Q2 y/y was +79%.
2. "One giant raised ~$100B of debt" was NOT supported. Replaced by: Amazon, Alphabet, Meta and Oracle together issued close to $200B of bonds this year (web: ~$194B through 7 Jul, Bloomberg-sourced via an aggregator). Alphabet's own bond sales found: ~$15B (Feb), $25B, ~$3.6B yen (May).
3. Removed "Alphabet ~$30.5B stock issuance": web found no Alphabet equity offering, so the vault row conflicts. Check that vault row (stack_unit_register, Alphabet Q2 2026 capex).
4. Removed "one chip maker says supply caps growth at ~70% vs demand ~140%": not found anywhere. Memory "booked into 2027" is now attributed to "my tracker" (single source, the vault). Web confirms HBM and CoWoS sold out for 2026.
5. "Cloud revenue +40%" in the tracker (stack_pulse C5, cloud_growth_pct 40.2) looks like AWS + Azure only; Google Cloud grew +82%. Script now says Amazon's and Microsoft's clouds ~40%, Google faster. The capex-vs-cloud gap is still large.
6. "Biggest cloud providers each ~$500B backlog" -> "Amazon and Google each ~$500B" (Microsoft's backlog is not in the film).

## ADDED nuance
- C3 power: ~30% of MW due in 12 months has documented secured power (1,688 of 5,598 MW). If partial arrangements count, ~18% has none. The film says both.

## STILL SINGLE-SOURCE (vault only; fine for "I track", check before posting)
- 106 sites, 77,345 MW planned, 7,826 MW operating. Register is US-heavy.
- Hyperion first 2 GW slipped ~2 years (2028 -> ~2030); Project Jupiter ~7 months behind (pipeline denied twice).
- UK: 5 tracked sites, ~672 MW planned, none operating. One UK row (Cambois) is labelled "operating" with 0 MW operating and a 2028 first-power date: likely a label error, fix in the vault.
- C4: every maker reporting book-to-bill is above 1.2.
- Meta El Paso 1 GW moved into an 80/20 JV with BlackRock.
- Amazon: $50B equity into OpenAI alongside OpenAI's $100B AWS expansion (the circular-financing point).

## EXTERNAL (checked once, 21 Oct)
- IEA Energy and AI (Apr 2025): ~415 TWh in 2024 (~1.5%) to ~945 TWh by 2030 (~3%); ~20% of planned sites could face grid delays. Newer IEA edition not checked.

## Compliance
- Education only. No tickers, price targets or advice on screen. No portfolio weights or £ shown (percentages-only rule).
- Disclosure line kept: "I may hold some of the companies in this theme."
- Photo credits (if any images) go in the description. No standalone .srt unless re-exported.

## Known small mismatch in the finished video (v1)
- Q1 chart shows the third chip maker at +221% (AI revenue growth); the voiceover says "between one hundred and two hundred percent". Fix options: pick up one sentence in the voice (about 3p) or change the bar label. Everything else on screen matches the voiceover.
- Visuals use a generated background (no photos), so there are no photo credits to add.
- Captions are burned in (word-highlighted). No separate .srt exists, so there is nothing to go out of sync.
