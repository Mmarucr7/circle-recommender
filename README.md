# Circle recommender

An API that recommends Lean In Circles a member could join. Each recommendation is a Circle that is relevant
to her, active, and has room for her, plus one short sentence written for the member explaining why.

```
GET /users/7/recommendations?limit=3
→ 1. Women Who Lead   "Matches your interest in leadership skills, and members posted 11 times this month."
  2. Speak Up Circle  "Matches your interest in public speaking and leadership skills, and members posted 8 times this month."
  3. Board-Ready Women "Matches your interest in leadership skills, and meets near you in Seattle."
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11 or newer. It installs Python 3.12 for
  you if needed.
- `make` and `curl`. On macOS, `make` comes with the Xcode command line tools (`xcode-select --install`).

## Setup

```bash
make setup   # install pinned dependencies from uv.lock
make seed    # build data/app.db from data/seed/ (safe to re-run)
make run     # serve on http://127.0.0.1:8000
```

Open **http://127.0.0.1:8000/docs** to try the API in the browser.

## Try the scenarios

The dataset plants four scenarios. With the server running:

```bash
# Cold start: no interests, no memberships, empty profile
curl -s "localhost:8000/users/42/recommendations?limit=5"
```
Expect `"strategy": "cold_start"` and five active virtual or hybrid Circles, each on a different topic, explained
like "An active virtual Circle on sponsorship & mentorship where members posted 11 times this month, a great
place to start."

```bash
# Obvious matches: interested in leadership skills and public speaking, lives in Seattle
curl -s "localhost:8000/users/7/recommendations?limit=3"
```
Expect #5 Women Who Lead first and #6 Speak Up Circle second.

```bash
# Duplicates: interested in negotiation; Circles 10, 11, 12 are near-identical
curl -s "localhost:8000/users/15/recommendations?limit=5"
```
Expect exactly one of them: #11 The Negotiation Table, ranked first.

```bash
# Full / inactive: interested in getting promoted
curl -s "localhost:8000/users/23/recommendations?limit=3&debug=true"
```
Expect #22 Level Up Collective first. In `debug.filtered_out`, #20 is `FULL` and #21 is `INACTIVE` (and `UNLISTED`).

Errors share one shape:

```bash
curl -s "localhost:8000/users/9999/recommendations"     # 404 {"error": {"code": "user_not_found", ...}}
curl -s "localhost:8000/users/7/recommendations?limit=0" # 422 {"error": {"code": "validation_error", ...}}
```

## API

`GET /users/{user_id}/recommendations?limit=10&debug=false`

| Field | Meaning |
| --- | --- |
| `strategy` | `personalized`, `blended` (profile signals mixed with popular, accessible Circles) or `cold_start` |
| `reference_time` | The "now" used for recency: the newest activity in the dataset |
| `recommendations[].explanation` | One sentence for the member, at most 140 characters |
| `recommendations[].reasons` | `{code, detail}` pairs behind the ranking, strongest first |
| `debug` (with `debug=true`) | Confidence, weights, per-Circle feature scores, and every filtered Circle with its reason codes |

`GET /health` returns `{"status": "ok"}`.

## Tests, linting and evaluation

```bash
make test       # pytest: scenarios, guarantees, explanation rules, features, API
make lint       # ruff check + ruff format --check
make typecheck  # mypy --strict
make evaluate   # re-seed, print top 5 for scenario + sample members, run checks, write docs/SAMPLE_OUTPUT.md
```

`make evaluate` exits non-zero if any check fails. The committed [docs/SAMPLE_OUTPUT.md](docs/SAMPLE_OUTPUT.md)
shows the results without running anything.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `CIRCLES_DB_PATH` | `data/app.db` | Database location |
| `CIRCLES_REFERENCE_TIME` | newest activity timestamp | Override "now" when seeding, e.g. `2026-09-21T00:00:00Z` |

All weights and thresholds live in [`src/circle_recommender/config.py`](src/circle_recommender/config.py).

## Project structure

```
schema.sql                     tables, constraints, indexes
data/seed/                     provided dataset, unchanged (generate.mjs reproduces it byte for byte)
src/circle_recommender/
  config.py                    every weight, threshold and setting
  api/                         FastAPI app, routes, response models, error handlers
  services/                    one request: load member and Circles, run the pipeline
  recommender/                 pure, deterministic logic, no I/O
    filters.py                 hard filters with reason codes
    features.py                topic, activity, location, profile, openness signals
    scoring.py                 confidence, strategy, weight blending
    diversify.py               one per dedupe cluster, per-topic cap
    explain.py                 template explanations from reason codes
    dedupe.py, activity.py     seed-time clustering and activity scoring
    pipeline.py                ties the steps together
  db/                          read-only connection, queries, idempotent seed
scripts/evaluate.py            scenario checks and sample output
tests/                         pytest suite
docs/                          design, schema, data notes, sample output
```

## Documentation

- [docs/DESIGN.md](docs/DESIGN.md): technical design, signals, tradeoffs, production plan
- [docs/SCHEMA.md](docs/SCHEMA.md): ER diagram, schema reasoning, index justifications
- [docs/DATA_NOTES.md](docs/DATA_NOTES.md): dataset profiling, thresholds and the evidence for each
- [docs/SAMPLE_OUTPUT.md](docs/SAMPLE_OUTPUT.md): evaluation results

## License

MIT, see [LICENSE](LICENSE).
