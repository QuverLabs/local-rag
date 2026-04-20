# Findings 0004 — Weight tuning is not a calibration lever

**Type:** negative result (saved per CLAUDE.md: „Jeżeli jakaś ścieżka okazała się niepowodzeniem zapisz wnioski")
**References:** runs 0001 (baseline), 0002 (pure semantic), 0003 (pure BM25)
**Commit:** `971195bd5fb5c2c1dcfc82819c79c2c6c0148dad` (worktree dirty while building benchmark infra)

---

## Hypothesis under test

Before running anything I observed that earlier ad-hoc probes (three sanity
queries run against `vector_weight=0.5/0.5`, `1.0/0.0`, `0.0/1.0`) returned
numerically identical scores across all three configurations. The natural
hypothesis: **`memory_set_option` silently ignores weight changes** — and if
true, the entire plan to „calibrate weights" collapses.

## Method

Ran the frozen 18-query benchmark three times against the same live index,
changing only `vector_weight` / `text_weight`. No re-ingest, no code changes,
no query changes. All three runs used `min_score=0.0` so top-K ordering was
captured raw.

| Run | vector | text |
|---|---|---|
| 0001 baseline | 0.5 | 0.5 |
| 0002 pure-semantic | 1.0 | 0.0 |
| 0003 pure-bm25 | 0.0 | 1.0 |

## Results

### The options *do* take effect — partially

Top-K scores shifted substantially. Example (Q01 `renowacja dachu bez zrywania starego pokrycia`, top-1 hit):

| Run | Top-1 score |
|---|---|
| Baseline (0.5/0.5) | 0.9556 |
| Pure semantic (1.0/0.0) | 1.4112 |
| Pure BM25 (0.0/1.0) | 1.9112 |

Ordering inside top-K also changed for some queries — `index.md` rose into
top-3 under pure-semantic / pure-BM25 where it wasn't under hybrid.
**Conclusion: `memory_set_option` is functional, the earlier probe was
insufficient.**

### But retrieval quality on this benchmark is insensitive to weight

Aggregate metrics are **identical to three decimal places** across all three
configs:

| Category | N | Hit@1 | Hit@3 | MRR |
|---|---|---|---|---|
| A | 6 | 83% | 100% | 0.889 |
| B | 4 | 75% | 100% | 0.875 |
| C | 4 | 75% | 75% | 0.750 |
| D | 3 | 0% | 0% | 0.000 |
| E | 1 | 100% | 100% | 1.000 |

No failing query gets fixed by moving to pure-BM25 or pure-semantic, and no
passing query breaks. **Weight tuning does not shift outcomes on this
benchmark.**

### Q14 — BM25 channel is completely cold on `100 000 m²`

Query 14 (`100 000 m²`) is our BM25 health probe. The string is physically
present in `uslugi/serwis-membran-pvc.md`, yet:

| Run | Top-1 | Score |
|---|---|---|
| Baseline | realizacje.md | 0.8420 |
| Pure semantic | realizacje.md | 0.8420 |
| Pure BM25 | realizacje.md | 0.8420 |

Identical to four decimals across all three runs. When `vector_weight=0.0,
text_weight=1.0` returns the same results as `vector_weight=1.0,
text_weight=0.0`, the **BM25 channel is contributing zero** for this query —
the FTS5 tokenizer isn't matching `100 000` or `m²` to any indexed token for
this file. Semantic-only retrieval pulls the wrong files because „100 000"
is a generic „large area" signal for the model, not a precise anchor.

Queries 11, 12, 13 (PN-EN 795, phone number, PRO-Leak Control) do hit —
those are tokens without whitespace inside the literal. The break is
specifically for numeric strings with internal whitespace and/or the `²`
glyph.

## Conclusions

1. **Do not spend further effort tuning `vector_weight` / `text_weight`.**
   The mechanism works but no realistic weight combination moves our
   benchmark metrics. Future PRs that change only weights should not claim
   quality improvements without a benchmark run showing one.

2. **The two levers that matter next are:**
   - **Chunking + prefix change** (README already flags this): switch
     `memory_add_file` → `memory_add_text` with `passage: ` prefix at
     ingest and `query: ` prefix at retrieval. The e5-instruct model was
     trained for this protocol and we're currently ignoring it. Expected
     impact: category A/B top-1 scores and A-vs-D discrimination gap.
     Requires re-ingest (acceptable per CLAUDE.md).
   - **Ingest-time text normalization for numeric exact strings.** For the
     FTS5 channel to match Q14, the indexed text would need to carry either
     `100000` or `100 000` tokenized as a single term, and `m²` aliased to
     `m2`. Candidates: Unicode normalization pass, digit-group-collapse,
     unit aliasing. Requires re-ingest.

3. **`min_score` threshold calibration is independent of weights and worth
   doing on its own.** Baseline data: nonsense queries (category D) score
   avg top-1 = 0.8180, category B scores 0.8827. A threshold of ~0.85 would
   cleanly filter most nonsense without cutting valid B hits. But this is a
   post-filter decision and doesn't require re-indexing — safe to leave for
   after the ingest rewrite.

## What *not* to do as follow-up

- Don't run more weight-only benchmarks „just to be sure". We have three
  data points and a mechanistic explanation.
- Don't touch `queries.toml`. The exact-string failure on Q14 is a real
  signal we want to keep measuring across future changes; „fixing" it by
  rewording the query is exactly the anti-pattern CLAUDE.md warns against.
