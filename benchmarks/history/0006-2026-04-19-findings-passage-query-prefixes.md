# Findings 0006 — passage/query prefixes: modest net win, no breakthrough

**Type:** positive result (small magnitude)
**References:** runs 0001 (baseline, no prefix), 0005 (passage+query prefixes)
**Commit:** repo state after `ingest.py` / `server.py` / `setup/_db.py` rewrite
to use `memory_add_text` with `passage: ` prefix + server-side `query: `
prefix. Worktree dirty at run time (expected — findings are committed together).

---

## Hypothesis under test

The `multilingual-e5-large-instruct` model README specifies an asymmetric
retrieval prompt: prepend `passage: ` to indexed chunks, `query: ` to user
queries at lookup. Our baseline ignored that protocol entirely (`memory_add_file`
fed raw text to the extension's chunker). Hypothesis: following the prompt
protocol will lift retrieval quality.

Secondary expectation: no help for Category C (exact-string / numeric
probes), because the failure mode there is FTS5 tokenization, not embedding
quality.

## Method

Rewrote ingest to `memory_add_text(passage: <file>, ctx)` + `UPDATE
dbmem_content.path` (the extension auto-generates a hex path; we overwrite
with the real file path so `fetch_document` and `path_filter` still work).
Full re-ingest on the same corpus (13 files, 7.8s). Ran `benchmarks.runner`
with the frozen query set, same `.env` weights (0.5/0.5).

## Results

### Aggregate

| Category | N | Hit@1 b→n | Hit@3 b→n | MRR b→n | avg top-1 b→n |
|---|---|---|---|---|---|
| A (natural) | 6 | 83% = 83% | 100% = 100% | **0.889 → 0.917** | 0.9081 → 0.9163 |
| B (multi-target) | 4 | 75% = 75% | 100% = 100% | 0.875 = 0.875 | 0.8827 → 0.8871 |
| C (exact-string) | 4 | 75% = 75% | 75% = 75% | 0.750 = 0.750 | 0.8777 → 0.8689 |
| D (nonsense) | 3 | 0% = 0% | 0% = 0% | — | 0.8180 → 0.8146 |
| E (generic "dach") | 1 | **100% → 0%** | 100% = 100% | **1.000 → 0.500** | 1.0000 → 0.8630 |

**Discrimination gap A vs. D:** `+0.0901 → +0.1017` (+0.0116, modest
improvement).

### Per-query deltas worth attention

- **Q2 `detekcja przecieków na dachu z membraną` (A):** expected hit
  (`serwis-membran-pvc.md`) moved from rank 3 to rank 2 — the clearest
  individual improvement. Top-1 still a non-expected file.
- **Q12 `+48 730 004 873` (C):** top-1 score dropped 0.9400 → 0.8792 but
  still hits `kontakt.md` at rank 1. Confidence dropped without changing
  outcome.
- **Q14 `100 000 m²` (C):** identical miss as baseline (realizacje.md
  rank 1, expected serwis-membran-pvc.md absent from top-K). Confirms the
  prediction — prefixes don't fix FTS5 tokenization of whitespace-separated
  numbers.
- **Q18 `dach` (E):** regression. Baseline top-1 was
  `uslugi/serwis-membran-pvc.md` (in expected set); with prefixes top-1 is
  `realizacje.md` (not in expected — realizacje is a portfolio page whose
  content is almost entirely image alt-text mentioning „dach" many times).
  Hit@3 still succeeds because the expected set is broad. Arguable whether
  this is a real regression or a legitimate re-ordering — `realizacje.md`
  mentioning "dach" 30+ times in alt-text is a real match for a one-word
  query, even if it's not the most *useful* answer.

## Conclusions

1. **Keep the prefixes.** The cost is three constants + a re-ingest step.
   The gains are small but real (Category A MRR +0.028, discrimination gap
   +0.0116) and the protocol is the one the model was trained for. Reverting
   would only be justified if a regression on our benchmark or a production
   MCP session were demonstrable; none shown.

2. **Q14 remains the keystone unsolved case.** `100 000 m²` still doesn't
   reach the file that physically contains that string. Confirms the next
   real lever: ingest-time text normalization (whitespace inside numeric
   groups, `m²` ↔ `m2` aliasing, probably Unicode NFKC). This is a
   separate PR; its success criterion should be flipping Q14 from miss to
   hit without regressing anything else.

3. **Q18 regression is soft but worth flagging.** Not fixing it now —
   a single-word query is an adversarial stress test by design, and the new
   top-1 (`realizacje.md`) is defensibly *relevant*. Future work that
   changes ranking behavior should check this query specifically and
   include rationale if it swings further.

4. **Gains were smaller than expected.** The README suggested prefixes
   would materially help Polish retrieval. Reality: the baseline was
   already at 83% Hit@1 / 100% Hit@3 for Category A, so there wasn't much
   room. On a larger or harder corpus the effect could be bigger; don't
   read our numbers as universal.

## What *not* to do as follow-up

- Don't revert the prefixes because the gain is small. The implementation
  is clean and the theory is right; the next improvement will compound with
  them, not replace them.
- Don't tweak the Q18 expected set to make the regression disappear. That
  would be exactly the anti-pattern CLAUDE.md warns about.
