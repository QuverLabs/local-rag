# local-rag retrieval benchmark

Measures *whether changes move the needle*, not how low we can push the loss.
The rules of the house:

- **Don't curate data for the benchmark.** `queries.toml` is frozen. Adding
  entries to chase a failing case is exactly the anti-pattern we're avoiding.
  New queries only when a new *class of phenomena* emerges; call it out in
  the commit that introduces them.
- **Don't modify production code to make the benchmark happier.** The runner
  calls the same `_search` helper `server.py` exposes to MCP. No test hooks,
  no `if BENCHMARK_MODE` branches, no special fixture paths.
- **History is append-only.** Negative results and dead ends are recorded
  with the same care as wins — they prevent re-walking the same path.

## Layout

```
benchmarks/
├── queries.toml              # frozen query set (18 queries, 5 categories)
├── runner.py                 # run the benchmark → history/NNNN-*.md
├── history/                  # chronologically-ordered reports (NNNN prefix)
└── README.md                 # this file
```

## Running

```bash
# Default — use whatever `.env` declares for weights.
uv run python -m benchmarks.runner --label <slug>

# Override weights ad-hoc (e.g. for a weight-sensitivity probe).
uv run python -m benchmarks.runner --label pure-semantic \
  --vector-weight 1.0 --text-weight 0.0
```

Each run writes `history/NNNN-YYYY-MM-DD-<label>.md` — one markdown file
containing: commit hash, worktree-dirty flag, active parameters, per-category
metrics, and per-query top-K hits.

## Metrics

- **Hit@1 / Hit@3** — did any expected path appear at rank 1 / within
  top-3? (Categories A, B, C, E only — nonsense queries skip this.)
- **MRR** — mean reciprocal rank of the first expected hit.
- **avg top-1 score** — mean of rank-1 scores across the category. For
  category D (nonsense) this is the *only* metric; it probes `min_score`
  calibration.
- **Discrimination gap A vs. D** — avg A top-1 minus avg D top-1. Higher
  means nonsense is scored measurably lower than on-topic content, so a
  `min_score` threshold can cleanly separate them.

## When to run

Per `AGENTS.md`: a benchmark run (with results committed) is required on any
PR that can affect retrieval quality — chunking, model, extensions, prefixes,
hybrid weights, DB schema, anything in the ingest or search path. README
tweaks, new MCP tools that don't touch retrieval, and CI changes do not need
a benchmark.

## Reading history

The `history/` directory is chronological (`NNNN` prefix). Three kinds of
file live there:

- **Runs** — output of `runner.py`. Named e.g. `0001-2026-04-19-baseline.md`.
- **Findings** — written by hand when a direction has been tested and we
  want to record the conclusion (positive or negative) so future-us doesn't
  re-litigate it. Named `NNNN-YYYY-MM-DD-findings-<topic>.md`.
- **Index** — none yet; if the list grows unwieldy we can add one.

To compare two runs, open them side by side. Changes in per-category
metrics tell you whether the change moved quality; changes in per-query
scores tell you *where* it moved.
