# logsentry

AI-assisted log clustering and root-cause summarization. Point it at a log
file, get back a Markdown report grouping repeated errors by pattern —
plus, if you have an API key, a short root-cause / next-step note per
cluster written by Claude.

- **Offline by default.** Clustering uses only regex normalization and
  Python's standard library — no network calls, no dependencies beyond
  `click`.
- **AI-assisted summary.** If `ANTHROPIC_API_KEY` is set, the top clusters
  (level, template, count, sample lines) are sent to Claude, which returns
  a short bullet list of likely causes and next steps.
- **Fails gracefully.** No API key, no `anthropic` package, or a network
  error — logsentry just ships the offline frequency report.

## How clustering works

Log messages rarely repeat verbatim — timestamps, request IDs, hostnames,
and line numbers change each time. logsentry normalizes those variable
parts into placeholders (`<num>`, `<uuid>`, `<ip>`, `<hex>`, `<path>`,
`<str>`) before grouping, so:

```
Connection refused to db-primary:5432
Connection refused to db-primary:5433
```

both collapse to the template `Connection refused to db-primary:<num>` and
count as one cluster of 2, instead of two separate one-off lines. Note
that hostnames themselves are left as-is (there's no safe generic pattern
for arbitrary hostnames), so `db-primary` vs `db-replica` would still be
counted as separate clusters.

## Install

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
# Offline cluster report
logsentry examples/sample.log -o report.md

# With an AI-written root-cause summary
export ANTHROPIC_API_KEY=sk-ant-...
logsentry examples/sample.log -o report.md

# Force offline even if a key is set
logsentry examples/sample.log --no-ai

# Only cluster ERROR and CRITICAL lines, top 10 clusters
logsentry examples/sample.log --level ERROR --level CRITICAL --top 10
```

## How it works

1. `parser.py` reads raw lines and extracts a level (`ERROR`, `WARN`,
   `INFO`, ...) and message from a few common log layouts, keeping
   anything unrecognized as level `UNKNOWN` rather than dropping it.
2. `clustering.py` normalizes each message (numbers, UUIDs, IPs, hex
   blobs, quoted strings, file paths → placeholders) and groups records
   by `(level, normalized template)`, sorted by descending frequency.
3. `generator.py` renders the clusters into Markdown. If an API key is
   available, it also sends the top clusters to Claude for a root-cause
   summary, prepended to the frequency report.
4. `cli.py` wires it together behind a `logsentry` command built with
   `click`.

## Development

```bash
pip install -r requirements.txt
pytest
```

Tests cover parsing (multiple log formats, unknown lines), clustering
(normalization rules, sort order, sample capping), and the generator's
offline fallback path — no network access required.

## Project layout

```
src/logsentry/
  parser.py      # raw line -> LogRecord(level, message, timestamp)
  clustering.py  # normalization + grouping into Cluster objects
  generator.py   # Markdown rendering + optional Claude root-cause summary
  cli.py         # click-based command line entry point
tests/           # pytest suite, no network required
examples/        # sample.log used by the demo and as a manual test fixture
```

## License

MIT — see [LICENSE](LICENSE).
