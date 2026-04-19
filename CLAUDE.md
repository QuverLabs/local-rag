# Working priorities for this repo

- **Retrieval quality > everything else.** Don't optimize for iteration speed
  or "less code" at the expense of search-result quality. If a change improves
  relevance, even slightly, it's wanted.
- **Re-ingest is fine.** Don't shy away from changes that require re-indexing
  the database (chunking, `passage:` / `query:` prefixes, model swap, extension
  bump). Propose them outright when you think they raise quality — a one-minute
  re-ingest is an acceptable cost.
