# Design: recommending Circles to join

## 1. What was built

`GET /users/{id}/recommendations` returns ranked Circles, each with one member-facing sentence and reason codes.
Pure, deterministic functions (`recommender/`) run over SQLite, with slow-changing Circle features computed at seed
time: candidates → hard filters (each with a reason code) → five features in [0, 1] → weighted sum → one result per
dedupe cluster, at most 2 per topic → template explanation. `?debug=true` exposes every score, weight and filter.

## 2. Signals

| Used | Weight* | Why |
| --- | --- | --- |
| Topic match: stated interests vs primary topic (1.0) or tag (0.4); topics of joined Circles at half strength | 0.40 | Strongest statement of intent |
| Activity: log-scaled posts, chat, engagement per post; recency decay, half-life 14 days | 0.25 | Members join for live connection |
| Format and location fit (in-person needs the same metro; hybrid boosted when local) | 0.15 | An unreachable Circle is not an option |
| Profile keywords (bio, job title → topics, small lexicon) | 0.10 | Light: bios are short and generic |
| Openness: seats left, uncapped size vs 15, open join policy | 0.10 | Room for the member to actually join |

\*Personalized weights. New members (≤30 days) move 0.05 from profile to openness. Cold start: activity 0.5,
location 0.3, openness 0.2.

**Not used:** photos, names, company or any demographic attribute (fairness; irrelevant to fit); cover images
(missing on very active Circles); Networks and industry (nothing to match); tenure and Circle age (inconsistent
timestamps). **Hard filters:** full; inactive (no posts in 30 days or >45 days silent, inside the data's 20→227-day
gap); unlisted; in-person in a known other metro; already joined, or a near-duplicate of a joined Circle.

**Confidence, not eligibility.** `c = 0.7·interest evidence + 0.3·completeness`, where joined-Circle topics can
supply at most half the interest evidence. Weights are blended as `c·personalized + (1−c)·cold start`, so a sparse
profile still gets a full list. Strategy: `cold_start` (no interests, no memberships), `personalized` (c ≥ 0.75),
otherwise `blended`.

## 3. Scenarios

| User | Result |
| --- | --- |
| 42, cold start | Ten active Circles across ten topics, virtual and hybrid first: "An active virtual Circle on sponsorship & mentorship…" |
| 7, obvious | #5 Women Who Lead first (local hybrid), #6 Speak Up Circle second; in-person Circles in other cities are filtered |
| 15, duplicates | Only #11 of {10, 11, 12}: one result per cluster, highest score wins; #12 is in-person in Denver |
| 23, full/inactive | #20 `FULL`, #21 `INACTIVE` + `UNLISTED`; #22 Level Up Collective ranks first |

`make evaluate` asserts these, plus invariants for all 100 members (`SAMPLE_OUTPUT.md`).

## 4. Tradeoffs

- **Rules over ML.** 100 users and no impressions or join outcomes: nothing to train on. Transparent weights can
  be explained, debugged and defended, and they become the baseline for a learned ranker later.
- **Templates over LLM text.** Every clause maps to a reason code and every number to a reason detail (tests
  enforce this), so an explanation cannot claim something untrue. The cost is less varied wording.
- **Seed-time features over per-request.** Activity and capacity change slowly; reads dominate. Staleness is
  bounded by refresh frequency, and capacity must be re-checked at join time anyway.
- **SQLite over Postgres.** Zero setup for reviewers; plain SQL ports directly. Not suitable for concurrent writes.
- **Location proxy.** Circles have no location, so a Circle's location is its leader's. An unknown location is
  never filtered, only scored neutrally (0.5).

## 5. Production at scale

Postgres with read replicas; batch-precomputed recommendations updated incrementally from join, post and capacity
events; per-user cache invalidated by those events; embedding topic matching with approximate nearest-neighbour
search; impression and join logging to A/B-test weights, then learning-to-rank; fairness and coverage monitoring
(exposure by Circle size and age) so small or new Circles are not starved; a conditional update at join time
(`… WHERE member_count < max_members`) so two members cannot take the last seat.

## 6. With more time

Real Circle location and meeting-time fields; re-ranking so each stated interest is covered early; an opt-in path
for affinity Circles (topic-less identity or regional groups) rather than ranking them on activity alone.

## How I used AI tools

### Where AI helped

### What I verified or changed

### Decisions I made myself
