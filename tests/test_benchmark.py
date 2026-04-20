from __future__ import annotations

from pathlib import Path

from benchmarks.runner import _hit_position, _rel_path, _summarize


def test_hit_position_returns_one_based_position_of_first_match():
    expected = ["uslugi/foo.md"]
    actual = ["other/bar.md", "uslugi/foo.md", "uslugi/foo.md"]
    assert _hit_position(expected, actual) == 2


def test_hit_position_returns_none_when_no_match():
    assert _hit_position(["uslugi/foo.md"], ["other/bar.md"]) is None


def test_hit_position_empty_expected_returns_none():
    assert _hit_position([], ["other/bar.md"]) is None


def test_hit_position_matches_any_expected_entry():
    assert _hit_position(["a.md", "b.md"], ["x.md", "b.md"]) == 2


def test_rel_path_strips_notes_root(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    abs_path = tmp_path / "sub" / "file.md"
    abs_path.touch()
    assert _rel_path(str(abs_path), tmp_path) == "sub/file.md"


def test_rel_path_returns_original_when_outside_root(tmp_path: Path):
    outsider = "/somewhere/else/file.md"
    assert _rel_path(outsider, tmp_path) == outsider


def _fake_result(qid, category, query, expected, actual, latency_ms=1.0):
    return {
        "id": qid,
        "category": category,
        "query": query,
        "expected": expected,
        "actual": [{"path": p, "ranking": r} for p, r in actual],
        "latency_ms": latency_ms,
    }


def test_summarize_computes_hit1_hit3_mrr_per_category():
    results = [
        # Category A: first at pos 1, second at pos 2, third at pos 4 (not in top-3).
        _fake_result(1, "A", "q1", ["a.md"], [("a.md", 0.9), ("x.md", 0.7)]),
        _fake_result(2, "A", "q2", ["b.md"], [("y.md", 0.8), ("b.md", 0.7), ("z.md", 0.6)]),
        _fake_result(
            3,
            "A",
            "q3",
            ["c.md"],
            [("x.md", 0.6), ("y.md", 0.55), ("z.md", 0.5), ("c.md", 0.45)],
        ),
    ]
    summary = _summarize(results)
    a = summary["A"]
    assert a["n"] == 3
    # Hit at positions [1, 2, 4] -> hit1=1/3, hit3=2/3
    assert abs(a["hit1_rate"] - 1 / 3) < 1e-9
    assert abs(a["hit3_rate"] - 2 / 3) < 1e-9
    # MRR = (1/1 + 1/2 + 1/4) / 3
    assert abs(a["mrr"] - (1 + 0.5 + 0.25) / 3) < 1e-9
    assert abs(a["avg_top1_score"] - (0.9 + 0.8 + 0.6) / 3) < 1e-9


def test_summarize_discrimination_gap_between_A_and_D():
    results = [
        _fake_result(1, "A", "good", ["a.md"], [("a.md", 0.95)]),
        _fake_result(2, "D", "nonsense", [], [("random.md", 0.80)]),
    ]
    summary = _summarize(results)
    assert abs(summary["_discrimination_A_vs_D"] - (0.95 - 0.80)) < 1e-9


def test_summarize_skips_hit_metrics_when_expected_is_empty():
    """Category D (nonsense) has no expected paths; MRR/Hit should not pollute."""
    results = [
        _fake_result(1, "D", "nonsense", [], [("any.md", 0.70)]),
        _fake_result(2, "D", "more nonsense", [], [("other.md", 0.72)]),
    ]
    d = _summarize(results)["D"]
    assert d["n"] == 2
    assert d["hit1_rate"] == 0.0  # no expected -> no hits counted
    assert d["mrr"] == 0.0
    # But avg_top1_score is computed regardless — this is the point for D.
    assert abs(d["avg_top1_score"] - (0.70 + 0.72) / 2) < 1e-9


def test_summarize_handles_empty_actual_list():
    """When a query returns zero hits, it still counts as 1 query with no hit."""
    results = [_fake_result(1, "A", "q", ["a.md"], [])]
    a = _summarize(results)["A"]
    assert a["n"] == 1
    assert a["hit1_rate"] == 0.0
    assert a["avg_top1_score"] == 0.0
