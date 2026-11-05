# Design: recommending Circles to join

## What I built

`GET /users/{id}/recommendations` returns ranked Circles, each with one sentence for the member plus reason codes.
Pure, deterministic functions run over SQLite: candidates → hard filters → five features in [0, 1] → weighted sum →
one result per near-duplicate cluster, at most 2 per topic → template explanation. `?debug=true` shows every
score, weight and filtered Circle. `make evaluate` checks the four scenarios and all 100 members (`SAMPLE_OUTPUT.md`).

## Signals and why

| Signal | Weight* | Rationale |
| --- | --- | --- |
| Stated interests vs Circle topic (1.0) or tag (0.4); topics of Circles already joined at half strength | 0.40 | Strongest statement of intent |
| Activity: log-scaled 30-day posts, chat and engagement; recency decay (half-life 14 days) | 0.25 | Members join for live connection |
| Format and location: virtual fits all; in-person needs the same metro; hybrid boosted when local | 0.15 | An unreachable Circle is no option |
| Profile keywords (bio, job title) mapped to topics | 0.10 | Light: bios are short and generic |
| Room to join: seats left, size of uncapped Circles vs 15, open join policy | 0.10 | She has to be able to get in |

\*New members (joined ≤30 days ago) shift 0.05 from profile to room to join. Cold start: activity 0.5, location
0.3, room 0.2. **Completeness sets trust, not eligibility:** `c = 0.7·interest evidence + 0.3·completeness`
blends personalized and cold-start weights, so sparse profiles still get full lists.

**Hard filters** (activity and availability gate a Circle rather than just lowering it): full; inactive (no posts
in 30 days or >45 days silent, chosen inside the data's 20→227-day gap); unlisted; in-person in a known other
city; already joined, or a near-duplicate of one. **Not used:** photo, name, company, demographics (fairness;
irrelevant to fit); cover image (missing on very active Circles); descriptions (one template per topic) and
industry (nothing to match); Networks (absent); tenure (timestamps inconsistent).

## Tradeoffs

- **Rules over ML:** no join outcomes to learn from; transparent weights are a debuggable baseline.
- **Templates over LLM text:** every clause maps to a reason code (tested), so nothing untrue is claimed.
- **Seed-time features:** activity, capacity and duplicate clusters change slowly and reads dominate.
- **SQLite over Postgres:** zero setup for reviewers; the plain SQL ports directly.
- **Location proxy:** the leader's city stands in for the Circle's; unknown locations are never filtered.

## Production at scale

Postgres with read replicas; recommendations precomputed in batch and updated from join, post and capacity
events; per-user cache invalidated by those events; embedding-based topic matching with approximate
nearest-neighbour search over real descriptions and bios; impression and join logging to A/B-test weights, then
learning-to-rank; exposure monitoring by Circle size and age so small or new Circles are not starved; a
conditional update (`WHERE member_count < max_members`) so two members cannot take the last seat. Next: real
Circle locations, covering every stated interest early, and opt-in affinity Circles.

## How I used AI tools

### Where AI helped

### What I verified or changed

### Decisions I made myself
