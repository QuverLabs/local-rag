"""Run the frozen benchmark query set against the live local-rag index.

Produces a markdown report under ``benchmarks/history/`` carrying:

- commit hash and worktree-dirty flag of the repo at run time
- active retrieval parameters (weights, chunking, model, ...)
- per-category metrics (Hit@1, Hit@3, MRR, avg top-1 score)
- per-query top-K hits with expected vs. actual

The query set in ``queries.toml`` is frozen — changes require a rationale in
the commit that introduces them so history remains comparable over time.

The runner forces ``min_score = 0.0`` during measurement so we always see the
raw top-K ordering; the threshold is a post-filter, not a ranking signal.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path

from server import _search
from setup._db import load_env, open_memory_connection, require_env_path, set_option

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO_ROOT / "benchmarks"
QUERIES_PATH = BENCH_DIR / "queries.toml"
HISTORY_DIR = BENCH_DIR / "history"


def _git_head() -> tuple[str, bool]:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty_out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        )
        return sha, bool(dirty_out.strip())
    except Exception:  # noqa: BLE001 — best-effort; any failure (missing git, not a repo, ...) falls back
        return "unknown", False


def _next_run_number() -> int:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(p for p in HISTORY_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))
    if not existing:
        return 1
    return int(existing[-1].stem[:4]) + 1


def _rel_path(abs_path: str, notes_root: Path) -> str:
    """Return path relative to ``notes_root`` when inside, else original string."""
    try:
        return str(Path(abs_path).resolve().relative_to(notes_root)).replace(os.sep, "/")
    except ValueError:
        return abs_path


def _hit_position(expected: list[str], actual: list[str]) -> int | None:
    """Return the 1-based index of the first ``expected`` path found in
    ``actual``, or ``None`` if none match (also when ``expected`` is empty)."""
    if not expected:
        return None
    for i, path in enumerate(actual, 1):
        if path in expected:
            return i
    return None


def _summarize(results: list[dict]) -> dict:
    """Aggregate per-query results into per-category metrics.

    Returns one entry per category key (``A``, ``B``, ...), each holding
    ``n``, ``hit1_rate``, ``hit3_rate``, ``mrr``, ``avg_top1_score``.
    Also adds ``_discrimination_A_vs_D`` when both categories exist — the
    mean top-1 score of A minus D, a proxy for how well the retriever
    separates signal from noise.
    """
    buckets: dict[str, dict] = {}
    for r in results:
        b = buckets.setdefault(
            r["category"],
            {"n": 0, "hit1": 0, "hit3": 0, "mrr_sum": 0.0, "top1_scores": []},
        )
        b["n"] += 1
        paths = [a["path"] for a in r["actual"]]
        if r["actual"]:
            b["top1_scores"].append(r["actual"][0]["ranking"])

        pos = _hit_position(r["expected"], paths)
        if pos is not None:
            if pos == 1:
                b["hit1"] += 1
            if pos <= 3:
                b["hit3"] += 1
            b["mrr_sum"] += 1.0 / pos

    summary: dict = {}
    for cat, b in buckets.items():
        n = b["n"]
        scores = b["top1_scores"]
        summary[cat] = {
            "n": n,
            "hit1_rate": b["hit1"] / n if n else 0.0,
            "hit3_rate": b["hit3"] / n if n else 0.0,
            "mrr": b["mrr_sum"] / n if n else 0.0,
            "avg_top1_score": sum(scores) / len(scores) if scores else 0.0,
        }
    if "A" in summary and "D" in summary:
        summary["_discrimination_A_vs_D"] = summary["A"]["avg_top1_score"] - summary["D"]["avg_top1_score"]
    return summary


def _render_report(
    run_number: int,
    label: str,
    git_hash: str,
    git_dirty: bool,
    notes_root: Path,
    params: dict,
    results: list[dict],
    summary: dict,
) -> str:
    lines: list[str] = []
    lines.append(f"# Benchmark {run_number:04d} — {label}")
    lines.append("")
    lines.append(f"- **Run date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Commit:** `{git_hash}`" + (" _(worktree dirty)_" if git_dirty else ""))
    lines.append(f"- **Notes root:** `{notes_root}`")
    lines.append(f"- **Queries:** `{QUERIES_PATH.relative_to(REPO_ROOT)}` ({len(results)} total)")
    lines.append("")
    lines.append("## Parameters")
    lines.append("")
    for k, v in params.items():
        lines.append(f"- `{k}` = `{v}`")
    lines.append("")
    lines.append(
        "> Note: the runner forces `min_score = 0.0` during measurement so"
        " top-K ordering is captured regardless of the filter configured in"
        " `.env`. The `.env` value is recorded above for context but not"
        " applied here."
    )
    lines.append("")
    lines.append("## Summary per category")
    lines.append("")
    lines.append("| Category | N | Hit@1 | Hit@3 | MRR | avg top-1 |")
    lines.append("|---|---|---|---|---|---|")
    for cat in sorted(k for k in summary if not k.startswith("_")):
        s = summary[cat]
        lines.append(
            f"| {cat} | {s['n']} | {s['hit1_rate']:.0%} | {s['hit3_rate']:.0%} |"
            f" {s['mrr']:.3f} | {s['avg_top1_score']:.4f} |"
        )
    if "_discrimination_A_vs_D" in summary:
        gap = summary["_discrimination_A_vs_D"]
        lines.append("")
        lines.append(
            f"**Discrimination gap (A vs. D, avg top-1):** `{gap:+.4f}`  \n"
            f"_Higher is better — it means nonsense queries score noticeably"
            f" lower than on-topic ones, letting a threshold filter them._"
        )
    lines.append("")
    lines.append("## Per-query detail")
    lines.append("")
    for r in results:
        lines.append(f"### Q{r['id']:02d} [{r['category']}] — `{r['query']}`")
        lines.append("")
        exp = ", ".join(f"`{p}`" for p in r["expected"]) if r["expected"] else "_(nonsense — score only)_"
        lines.append(f"- **Expected:** {exp}")
        lines.append(f"- **Latency:** {r['latency_ms']:.1f} ms")
        if r["actual"]:
            lines.append("- **Top-K:**")
            for a in r["actual"]:
                marker = "✓" if a["path"] in r["expected"] else " "
                lines.append(f"  - [{marker}] `{a['ranking']:.4f}` — `{a['path']}`")
        else:
            lines.append("- **Top-K:** _(no results)_")
        lines.append("")
    return "\n".join(lines)


def _load_queries() -> list[dict]:
    with QUERIES_PATH.open("rb") as f:
        data = tomllib.load(f)
    queries = data["queries"]
    for q in queries:
        q.setdefault("expected", [])
    return queries


def _run(
    conn,
    queries: list[dict],
    notes_root: Path,
    k: int,
) -> list[dict]:
    results = []
    for q in queries:
        t0 = time.perf_counter()
        hits, _ = _search(conn, q["query"], limit=k, path_filter=None)
        dt = time.perf_counter() - t0
        results.append(
            {
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "expected": q["expected"],
                "actual": [{"path": _rel_path(h["path"], notes_root), "ranking": h["ranking"]} for h in hits],
                "latency_ms": dt * 1000,
            }
        )
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True, help="slug for the history file name")
    ap.add_argument("--vector-weight", type=float, default=None)
    ap.add_argument("--text-weight", type=float, default=None)
    ap.add_argument("--limit", type=int, default=10, help="top-K size to retrieve per query")
    args = ap.parse_args()

    load_env()
    notes_root = require_env_path("NOTES_DIR")
    memory_db = require_env_path("MEMORY_DB")
    extensions_dir = require_env_path("EXTENSIONS_DIR")
    model_path = require_env_path("MODEL_PATH")

    vector_weight = (
        args.vector_weight
        if args.vector_weight is not None
        else float(os.environ.get("MEMORY_VECTOR_WEIGHT", 0.5))
    )
    text_weight = (
        args.text_weight if args.text_weight is not None else float(os.environ.get("MEMORY_TEXT_WEIGHT", 0.5))
    )

    conn = open_memory_connection(memory_db, extensions_dir, model_path, check_same_thread=False)
    set_option(conn, "vector_weight", vector_weight)
    set_option(conn, "text_weight", text_weight)
    set_option(conn, "max_results", max(args.limit, 10))
    set_option(conn, "min_score", 0.0)  # always capture top-K regardless of .env threshold

    queries = _load_queries()
    results = _run(conn, queries, notes_root, args.limit)
    summary = _summarize(results)

    git_hash, git_dirty = _git_head()
    params = {
        "vector_weight": vector_weight,
        "text_weight": text_weight,
        "limit": args.limit,
        "env.MEMORY_MIN_SCORE": os.environ.get("MEMORY_MIN_SCORE", "(default)"),
        "env.MEMORY_MAX_TOKENS": os.environ.get("MEMORY_MAX_TOKENS", "(default)"),
        "env.MEMORY_OVERLAP_TOKENS": os.environ.get("MEMORY_OVERLAP_TOKENS", "(default)"),
        "model": model_path.name,
    }

    run_number = _next_run_number()
    report = _render_report(run_number, args.label, git_hash, git_dirty, notes_root, params, results, summary)

    stamp = datetime.now().strftime("%Y-%m-%d")
    # Replace path separators so a label like "passage/v2" doesn't try to write
    # into a non-existent subdirectory of HISTORY_DIR (FileNotFoundError).
    safe_label = args.label.replace("/", "-").replace("\\", "-")
    out_path = HISTORY_DIR / f"{run_number:04d}-{stamp}-{safe_label}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)

    # Quick stdout summary so you can eyeball the result without opening the file.
    for cat in sorted(k for k in summary if not k.startswith("_")):
        s = summary[cat]
        print(
            f"  {cat}: n={s['n']} hit1={s['hit1_rate']:.0%} hit3={s['hit3_rate']:.0%}"
            f" mrr={s['mrr']:.3f} avg_top1={s['avg_top1_score']:.4f}",
            file=sys.stderr,
        )
    if "_discrimination_A_vs_D" in summary:
        print(
            f"  discrimination A–D: {summary['_discrimination_A_vs_D']:+.4f}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
