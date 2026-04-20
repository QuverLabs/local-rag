"""Ingest- and query-time text normalization for FTS5 token alignment."""

from __future__ import annotations

import re
import unicodedata

# Lookbehind/lookahead so "100 dachów" (digit-space-letter) and "abc 123"
# (letter-space-digit) pass through; only digit-digit gaps collapse. After
# NFKC both NBSP (U+00A0) and narrow NBSP (U+202F) already fold to ASCII
# space, so we only need to match a regular space here.
_DIGIT_SPACE_DIGIT = re.compile(r"(?<=\d) (?=\d)")


def normalize(text: str) -> str:
    """Fold typographic variants so FTS5 sees the same token for `100 000 m²`,
    `100000 m2`, `100\u00a0000\u00a0m²` and `㎡` variants. Ingest and query
    must both call this; idempotent so double-calls are safe.
    """
    text = unicodedata.normalize("NFKC", text)
    return _DIGIT_SPACE_DIGIT.sub("", text)
