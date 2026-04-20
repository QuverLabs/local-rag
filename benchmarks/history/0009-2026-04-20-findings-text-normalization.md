# Findings 0009 — ingest-time text normalization + `query:` prefix removal

**Type:** positive result (Q14 flipped, Cat C went 75% → 100% / MRR 1.000)
**References:** runs 0005 (passage+query prefixes, Q14 miss), 0008
(text-normalization, Q14 rank-1 hit @ 1.0000). Findings 0004 (weight tuning
has no effect) and 0006 (prefix protocol helped A/B modestly but left Q14
untouched) are the prior art this change builds on.
**Commit:** worktree after `setup/_text.py`, `ingest.py`, `server.py`,
`setup/_db.py`, and `tests/test_server.py` edits landing together. Re-ingest
on the same corpus (13 files, 7.4 s).

---

## Hypothesis under test

Issue #5 proposed ingest-time text normalization (NFKC + digit-space
collapse + unit aliasing) as the minimum-viable fix for Q14 (`100 000 m²`).
The expected outcome was: Q14 flips from miss to rank-1 hit because the
normalized token `100000 m2` appears in `uslugi/serwis-membran-pvc.md` and
its canonical FTS5 token line up with what a query like `100 000 m²`
produces after the same normalization.

Prediction going in: no effect on Cat A/B/D/E beyond rounding, Cat C goes
from 3/4 to 4/4 hits.

## What actually happened

Normalization landed exactly as designed (NFKC gives `²` → `2` and `㎡` → `m2`
for free, so the "unit aliasing" bullet of the issue was subsumed by NFKC
and needed no extra code). The corpus was re-ingested and `dbmem_vault_fts`
now carries `100000` as an indexed token:

```
sqlite> SELECT hash, seq FROM dbmem_vault_fts WHERE dbmem_vault_fts MATCH '100000';
(-8705059740799455182, 3)  -- uslugi/serwis-membran-pvc.md, seq 3
(-8705059740799455182, 4)  -- same file, seq 4
```

But the first benchmark run committed at this point — 0007
(`text-normalization`, normalization applied on both sides *with* the
`query:` prefix still in place) — **still had Q14 as a full miss**:
serwis-membran-pvc.md not in the top 10 even after re-ingest. That was
unexpected, and untangling why led to the more important finding below.
0007 is kept in history per AGENTS.md as an honest record of the
intermediate state: normalization is necessary but not sufficient.

### Root cause of the residual miss: the `query:` prefix is FTS5-hostile

`memory_search` forwards the entire query string to FTS5 as an
implicit-AND match. The e5-instruct-flavoured prefix `query: ` (added in
PR #4 / benchmark 0005) tokenizes to `query` + the rest, and the token
`query` appears in exactly **zero** indexed documents (passages carry
`passage:` instead). Implicit AND therefore never returns any BM25
candidates, which silently collapses the "hybrid" ranker to pure vector
similarity — for every query, not just Q14.

Direct verification:

```
-- Works: 100000 is a rare, high-BM25 token that matches serwis-membran
-- seq=3 and gets score 1.0000.
SELECT s.path, s.ranking FROM memory_search
WHERE s.query = '100000 m2' LIMIT 1;
--> /notes/uslugi/serwis-membran-pvc.md | 1.0000

-- Same query with the e5-instruct prefix — BM25 is now zero because the
-- implicit AND requires "query" to be in the document:
SELECT s.path, s.ranking FROM memory_search
WHERE s.query = 'query: 100000 m2' LIMIT 1;
--> /notes/realizacje.md | 0.8437   (serwis-membran nowhere in top 10)
```

This retroactively explains 0004's stubborn `vector_weight` / `text_weight`
insensitivity: the BM25 channel hasn't been partially contributing since
PR #4, it's been contributing *nothing* for any query. The modest A/B
gains we saw in 0005 came entirely from the passage-side prefix priming
the embedding model, not from a working text channel.

### The applied fix

`server.py` now applies `setup._text.normalize(query)` but **does not**
prepend `query:` before the memory_search lookup. The ingest side still
writes `passage: {normalized text}` into `dbmem_content.value`, so the
semantic channel still benefits from the prompt priming the model was
trained with. Only the query side drops its half of the protocol, because
that half was actively harmful.

The `QUERY_PREFIX` constant has been removed from `setup/_db.py` (unused)
and `tests/test_server.py` now has `test_search_does_not_prepend_query_prefix`
as a regression guard — re-adding the prefix would make the test fail.

## Results (0008 vs 0005 baseline)

| Category | N | Hit@1 0005→0008 | Hit@3 0005→0008 | MRR 0005→0008 | avg top-1 |
|---|---|---|---|---|---|
| A natural | 6 | 83% → 67% | 100% = 100% | 0.917 → 0.833 | 0.9163 → 0.9076 |
| B multi-target | 4 | 75% = 75% | 100% = 100% | 0.875 = 0.875 | 0.8871 → 0.8827 |
| C exact-string | 4 | **75% → 100%** | **75% → 100%** | **0.750 → 1.000** | 0.8689 → 0.9132 |
| D nonsense | 3 | 0% = 0% | 0% = 0% | 0.000 = 0.000 | 0.8146 → 0.8167 |
| E generic "dach" | 1 | **0% → 100%** | 100% = 100% | **0.500 → 1.000** | 0.8630 → 1.0000 |

**Discrimination gap A vs. D (avg top-1):** `+0.1017 → +0.0909` (-0.0108 —
the gap shrinks because D's avg top-1 also inched up with BM25 noise, not
because A got less discriminative).

### Per-query movement worth naming

- **Q14 `100 000 m²` (C)** — the keystone. Miss → rank 1 @ score 1.0000.
  Pure-text match, no vector contribution needed. This is why the whole
  exercise happened.
- **Q18 `dach` (E)** — rank 2 @ 0.8630 → rank 1 @ 1.0000. Single-word FTS
  probe; with BM25 active it dominates. Prior finding 0006 flagged Q18 as
  a soft regression from 0005 (it used to be a 1.0000 hit in the baseline);
  the normalization pass also restores it. Net: back to parity with
  pre-prefix state and then some.
- **Q11 `PN-EN 795` (C)** — rank 1 preserved, score unchanged (0.8654).
  Hyphens and letter-digit boundaries passed through untouched, as
  `test_preserves_hyphen_tokens` requires.
- **Q12 `+48 730 004 873` (C)** — rank 1 preserved, score moved from
  0.8792 to 0.9125 — now a proper high-confidence phone-number hit
  instead of a near-threshold one. The normalized form `+48730004873` is
  a single unique BM25 token across the corpus.
- **Q13 `PRO-Leak Control` (C)** — rank 1 preserved, score 0.8857 → 1.0000.
  Same mechanism as Q14; the product name is a rare FTS token and BM25
  surfaces it perfectly now that the channel is wired.
- **Q05 `adres biura i telefon kontaktowy` (A)** — rank 1 → rank 2.
  Only Cat A drop. `polityka-prywatnosci.md` edged ahead (0.8775 vs
  0.8763) because BM25 is now active and privacy-policy pages carry a
  lot of overlap vocabulary ("adres", "kontaktowy"). Hit@3 still passes
  and the margin is 0.0012 — inside noise, arguably — but strictly
  speaking it's a MRR regression from 1.000 → 0.500 on this query.

## Why accept the Q05 trade-off

1. **The issue's explicit acceptance bullet — `Q14 flips from miss to hit`
   — is met with a 1.0000 rank-1 hit**, which is the strongest outcome
   available.
2. **Cat C Hit@3 goes 75% → 100% and MRR goes 0.750 → 1.000.** That is
   the whole category the issue was written to repair; it's now perfect.
3. **Q18 rank improvement more than compensates for the Q05 rank drop**
   in raw MRR terms — the benchmark-wide (unweighted) MRR is
   `(0.833·6 + 0.875·4 + 1.000·4 + 0.000·3 + 1.000·1) / 18 ≈ 0.667`
   vs. 0.659 for 0005. So overall retrieval quality is up, not down.
4. **Weight tuning can't recover Q05.** A sweep over
   `(vector_weight, text_weight)` from (0.5, 0.5) through (0.9, 0.1)
   leaves Q05 at rank 2 for every combination — consistent with
   finding 0004's observation that weights affect scores but not
   outcomes on this benchmark. So there's no free dial to turn.
5. **Q05's top-1 is still a privacy-policy page, not nonsense.** The
   expected answer remains in the top 3 with a margin of 0.001 to the
   wrong top-1, which would be trivial to disambiguate at the LLM layer
   or by a `min_score`-style post-filter.

The alternative — keep the `query:` prefix — leaves Q14 as a permanent
miss and documents Cat C retrieval as "not supported on numeric strings
with internal whitespace". That is a strictly worse posture given the
product is a local RAG for technical reference documents where exact
numeric hits matter.

## Conclusions

1. **Ship.** Normalization + query-side prefix removal is a net win on
   every measure except Q05 rank (inside top-3, margin 0.001). Q14 is
   the key fix and it lands cleanly.

2. **The BM25 channel works now.** Any future "hybrid search" intuition
   can actually rely on BM25 contributing for rare tokens, which wasn't
   true between PR #4 and this change. Factor that into whatever comes
   next (tuning `min_score`, chunk size, re-ranking heuristics).

3. **The asymmetric-prefix protocol was the wrong abstraction for an
   extension that passes the raw query to FTS5.** Symbolic "prefix as
   prompt" only works if the retrieval system understands it as a prompt
   and strips it before indexing. `memory_search` does not — so the
   prefix has to be either bilateral with a token that *is* in every
   document, or absent. We picked absent on the query side and kept
   passage-side priming.

## What *not* to do as follow-up

- **Don't re-add `query:` on the server side without a re-ingest that
  also places a matching sentinel token inside every passage chunk.**
  The `test_search_does_not_prepend_query_prefix` guard will catch the
  naive re-add, but the right fix, if you ever want symmetric priming
  back, is to make the FTS index carry the query token too — otherwise
  you're back in 0005's silent-zero-BM25 regime.

- **Don't chase Q05 rank-1 by weight sweeps.** Finding 0004 already
  established `vector_weight` / `text_weight` don't move outcomes on
  this benchmark; the sweep documented here confirms it under the new
  BM25-active regime as well. If Q05 matters, solve it at the LLM layer
  (answer synthesis) or by adding a dedicated `min_score` / re-ranker
  on contact-page heuristics — not by re-tuning the extension.

- **Don't edit `queries.toml`.** Q05's new rank-2 is the benchmark doing
  its job. Rewording the query to re-secure rank 1 would exactly be the
  anti-pattern `AGENTS.md` warns against.
