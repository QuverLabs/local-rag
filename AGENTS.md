# AGENTS.md

Operating rules for coding agents (and humans) working in this repository.
Complements `CLAUDE.md`, which holds project priorities.

## Benchmark discipline

Any PR that can change **retrieval quality** must include a fresh benchmark
run in `benchmarks/history/`, committed alongside the code change. The PR
description should reference the relevant run file(s) and note whether
category-level metrics moved (for better or worse).

Changes that **do** require a benchmark run:

- Ingest pipeline: chunking, text preprocessing, prefixes (`passage:` /
  `query:`), model swap, extension version bump.
- Retrieval path: changes to `server.py`'s `_search`, SQL in tool handlers,
  per-connection options, hybrid weight defaults, `min_score` defaults.
- Schema or DB structure affecting `dbmem_content` / `dbmem_vault` /
  `memory_search` shape or content.

Changes that **do not** require a benchmark run:

- New MCP tools that don't touch `_search` (e.g. the existing
  `local_rag_fetch_document` added alongside metadata fields).
- README, CLAUDE.md, AGENTS.md, other documentation.
- Benchmark infrastructure itself (runner, test fixtures, history
  formatting) — unless the change alters how metrics are computed.
- CI, packaging, bundling scripts, `pyproject.toml` dev-deps.

When unsure, run it — the baseline run takes <10 seconds.

## How to run

```bash
uv run python -m benchmarks.runner --label <short-slug>
```

`<slug>` should be a short description of the change under test, e.g.
`passage-prefix`, `chunk-512-100`, `min-score-0.85`. One run per experiment.
Never delete or rewrite existing history entries — add new ones.

Record negative results explicitly. If an approach turned out not to help
(or made things worse), write a `NNNN-YYYY-MM-DD-findings-<topic>.md` file
summarising *why* so the same path isn't re-walked later. The precedent is
`benchmarks/history/0004-2026-04-19-findings-weight-tuning.md`.

## Do not edit `queries.toml` to chase numbers

The frozen query set is intentional. If a change makes a previously-passing
query fail, that is the benchmark doing its job — investigate the
regression, don't rewrite the question.

Adding queries is allowed only when a new class of phenomena emerges that
isn't probed by the existing set; explain the addition in the commit
message.
