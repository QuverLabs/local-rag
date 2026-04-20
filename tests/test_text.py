"""Tests for setup._text.normalize.

normalize() runs on both sides of retrieval, so these cases guarantee that
FTS5 sees the same tokens regardless of which typographic variant of a
numeric / symbol-heavy string the caller supplies.
"""

from __future__ import annotations

from setup._text import normalize


def test_ascii_text_passes_through_unchanged():
    text = "renowacja dachu bez zrywania starego pokrycia"
    assert normalize(text) == text


def test_collapses_ascii_space_inside_number():
    # Q14 keystone: `100 000 m²` ↔ `100000` must share a token.
    assert normalize("powyżej 100 000 m kwadratowych").startswith("powyżej 100000 m")


def test_collapses_multiple_gaps_in_single_number():
    # A single re.sub pass must eat both gaps in "100 000 000".
    assert "100000000" in normalize("nawet 100 000 000 razy")


def test_collapses_non_breaking_space_inside_number():
    # NBSP (U+00A0) is common in Polish typography.
    assert normalize("kompleks 100\u00a0000 m") == normalize("kompleks 100 000 m")


def test_collapses_narrow_no_break_space_inside_number():
    # U+202F: NFKC folds it to ASCII space, then collapse fires.
    assert normalize("kompleks 100\u202f000 m") == normalize("kompleks 100 000 m")


def test_does_not_collapse_digit_letter_boundary():
    # "100 dachów" must stay; collapsing it would wreck prose tokenization.
    assert normalize("pokryliśmy 100 dachów") == "pokryliśmy 100 dachów"


def test_does_not_collapse_letter_digit_boundary():
    # Q11 `PN-EN 795` must survive — letter-space-digit is not a gap.
    assert normalize("norma PN-EN 795") == "norma PN-EN 795"


def test_preserves_hyphen_tokens():
    # Q11 / Q13 rely on hyphens passing through verbatim.
    assert normalize("PN-EN 795") == "PN-EN 795"
    assert normalize("PRO-Leak Control") == "PRO-Leak Control"


def test_phone_number_collapses_all_digit_gaps():
    # Q12: both sides collapse identically, so the hit survives.
    assert normalize("+48 730 004 873") == "+48730004873"


def test_nfkc_folds_superscript_two_in_unit():
    # NFKC maps U+00B2 ("²") → "2", so m² and m2 land on one token.
    assert normalize("powierzchnia 5 m²").endswith("m2")
    assert normalize("5 m²") == normalize("5 m2")


def test_nfkc_folds_single_char_square_m():
    # U+33A1 (㎡) decomposes via "m" + U+00B2 → "m2".
    assert normalize("5 ㎡") == normalize("5 m2")


def test_q14_variants_all_collapse_to_same_key():
    # Every Q14 phrasing must normalize to something that contains the
    # same numeric+unit token as the file form ("100000 m2").
    file_form = normalize("powyżej 100 000 m².")
    assert "100000 m2" in file_form
    for q in ["100 000 m²", "100000 m²", "100 000 m2", "100000 m2", "100\u00a0000\u00a0m²"]:
        assert "100000" in normalize(q) and "m2" in normalize(q), q


def test_idempotent():
    samples = [
        "plain ascii",
        "100 000 m²",
        "100\u00a0000 m²",
        "kompleksy magazynowe powyżej 100 000 m².",
        "PN-EN 795",
        "+48 730 004 873",
        "",
        "㎡",
        "100 dachów",
    ]
    for s in samples:
        once = normalize(s)
        assert normalize(once) == once, f"not idempotent for {s!r}"


def test_empty_string_returns_empty():
    assert normalize("") == ""
