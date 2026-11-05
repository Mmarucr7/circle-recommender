# Data notes (Phase 0)

Findings from profiling `data/seed/` before any application code was written. Every number below was
produced by a profiling pass over the seed files. The seed files are byte-identical to a fresh run of
`data/seed/generate.mjs`, which confirms the copy is unmodified.

## 1. Files and shape

| File | Rows | Key | References |
| --- | --- | --- | --- |
| `topics.json` | 22 | `id`, unique `slug` | none; `domain` is always `content` |
| `users.json` | 100 | `id` | `topic_interests[]` → `topics.slug` |
| `circles.json` | 40 | `id`, unique `slug` | `topic`, `tags[]` → `topics.slug` |
| `memberships.json` | 441 | (`user_id`, `circle_id`), no duplicates | → `users.id`, `circles.id` |
| `activity.json` | 386 | `id` | → `circles.id`, `author_user_id` → `users.id` |

Referential integrity is clean: no dangling user, circle or topic references, every post author is a member
of that Circle, every Circle has exactly one leader, and `circles.member_count` equals the number of
membership rows for every Circle.

## 2. Field profiles

### users (100)

| Field | Nulls | Notes |
| --- | --- | --- |
| `has_photo` | 0 | 62 true / 38 false. **Not used for ranking.** |
| `bio` | 53% | Only 10 distinct strings (6 template bios + 3 planted + null). |
| `job_title` | 24% | 20 distinct values. |
| `company` | 54% | 10 distinct values. |
| `industry` | 24% | 8 values. No Circle field to match it against, so it is not used. |
| `location` | 33% | 10 values: 9 cities plus `Remote`. One user per city string; no metro aliasing is needed in this data. |
| `joined_at` | 0 | 2024-10-02 .. 2026-09-20. 4 users joined in the 30 days before the reference time (42, 79, 92, 100). |
| `topic_interests` | 30 empty | Counts: 0 → 30 users, 1 → 23, 2 → 24, 3 → 23. All slugs valid. |
| `profile_completeness` | 0 | Values 0, 0.2, 0.4, 0.6, 0.8, 1.0 with counts 1, 3, 12, 37, 35, 12. Recomputable from the fields. |

Memberships per user: 0 → 1 user (42), 1 → 7, 2 → 11, 3 → 18, 4 → 16, 5 → 14, 6 → 15, 7 → 12, 8 → 4, 9 → 2.
User 42 is the **only** user with neither interests nor memberships. 29 other users have no stated
interests but do have memberships.

### circles (40)

| Field | Nulls | Notes |
| --- | --- | --- |
| `description` | 2 (27, 28) | Every non-null value is the template `A supportive circle for women focused on <topic label>.` |
| `topic` | 2 (27, 28) | All 22 topics are used: 4 topics have 3 Circles, 8 have 2, 10 have 1. |
| `tags` | 2 empty | Always valid slugs. Circle 17 repeats `difficult-conversations`. 10 Circles do not include their own topic in `tags`. |
| `cover_image_url` | 6 | Missing on 15, 16, 17, 26, 38, 39, which include some of the most active Circles (15, 39). Not a quality signal. |
| `format` | 0 | `in_person` 16, `hybrid` 14, `virtual` 10. |
| `access` | 0 | `public` 37, `unlisted` 3 (18, 21, 30). |
| `join_policy` | 0 | `open` 28, `request` 12. |
| `max_members` | 14 (35%) | Null means uncapped. Capped values 6..38, median 17. |
| `member_count` | 0 | 3..28, median 10.5. |
| `feed_posts_30d` | 0 | 0..20, median 6. Matches the count of `activity` rows in the last 30 days for every Circle. |
| `chat_messages_30d` | 0 | 2..215, median 36. |
| `last_activity_at` | 0 | 2026-01-29 .. 2026-09-20T18:00. |

**There is no Circle location field.** The only location data is on users.

### activity (386)

Posts span 2026-03-27 .. 2026-09-21; 39 of 40 Circles have posts (32 has none). `body` has 15 distinct
template strings, so post text carries no Circle-specific signal. Engagement per recent post
(reactions + comments + saves) is 11–19 for active Circles and about 3–9 for moderate ones.

### Timestamp consistency (data quality)

- 205 membership rows are dated before the member's own account `joined_at`.
- 140 membership rows are dated before the Circle's `created_at`; 7 posts predate their Circle.

The generator draws these timestamps independently. Consequence: **membership tenure and Circle age are not
trustworthy signals** and are not used. Account `joined_at` is used only to flag new members.

## 3. Reference time

| Source | Newest value |
| --- | --- |
| `activity.created_at` | **2026-09-21T00:00:00Z** |
| `circles.last_activity_at` | 2026-09-20T18:00:00Z |
| `memberships.joined_at`, `users.joined_at` | 2026-09-20T00:00:00Z |

`REFERENCE_TIME` defaults to the newest activity timestamp, **2026-09-21T00:00:00Z** (also the generator's
anchor). It can be overridden in configuration. Using the wall clock (November 2026) would push every Circle
past 45 days without activity and mark all of them inactive.

## 4. Capacity and "full"

A capacity field exists (`max_members`), so no threshold has to be inferred for capped Circles.

- **Full** = `max_members` is not null and `member_count >= max_members`. Exactly one Circle qualifies:
  **20 The Promotion Path (15/15)**.
- Nearly full (2 seats or fewer): 18 (unlisted), 38.
- **Uncapped Circles (14)** are never treated as full, per the data dictionary. Lean In's Circles guide
  describes Circles as "intentionally small to allow for meaningful connections" without giving a number.
  The dataset's own size bands top out at 15 for a medium Circle, and the median capped `max_members` is 17.
  So an uncapped Circle's *openness* feature tapers above a **soft size of 15 members** (affected: 1 with 24
  members). It is not filtered.

## 5. Activity and inactivity threshold

Days since last activity at the reference time (sorted):
`0.2, 0.2, 0.4, 0.7, 0.8, 1.0, 1.2, 2.0, 2.1, 2.1, 2.3, 2.9, 3.0, 3.0, 3.0, 3.1, 3.3, 3.3, 3.4, 3.5, 3.8, 4.0,
4.0, 5.0, 6.0, 7.0, 9.0, 9.0, 10.0, 11.0, 12.0, 14.0, 16.0, 17.0, 17.0, 18.0, 20.0, 20.0, 227.0, 235.0`

Posts in 30 days: `0, 0, 2, 2, 3, 3, 4, 4, 4, 4, 5 ×9, 6 ×3, 8 ×3, 9, 10, 10, 11 ×4, 12, 13, 14, 15, 16, 18, 20, 20`.
Chat in 30 days: 2..215; the two lowest values (2, 3) belong to the same two Circles.

The distribution is bimodal with an empty gap between 20 and 227 days. Lean In's guide says "Most Circles
meet monthly", so a healthy Circle shows activity at least about every 30 days.

**Inactive** = `feed_posts_30d == 0` **or** more than **45 days** since `last_activity_at`
(one missed monthly meeting plus two weeks of slack). Both rules select exactly the same two Circles,
**21 Career Climbers** (227 days) and **32 The Resilience Room** (235 days). The threshold sits in the middle
of the gap, so it is robust to small changes in the reference time.

Activity score inputs (each log-scaled against a fixed cap in config rather than the dataset maximum, so a
Circle's score does not move when another Circle changes): posts in 30 days, chat in 30 days, engagement
per recent post, and recency with exponential decay (half-life 14 days: 0 days → 1.0, 14 → 0.5, 20 → 0.37).

## 6. Location and format

Circles have `format` but no location. Proxy used: **a Circle's location is its leader's location**
(the README points to leaders' profiles as a derived signal). Leader location is known for 27 Circles and
unknown for 13 (2, 3, 4, 6, 10, 14, 15, 19, 20, 23, 24, 26, 32). `Remote` is treated as "no metro".

| Format | Member and Circle in same metro | Location unknown on either side | Different metros |
| --- | --- | --- | --- |
| `virtual` | fit 1.0 | fit 1.0 | fit 1.0 |
| `hybrid` | fit 1.0 | fit 0.7 | fit 0.7 |
| `in_person` | fit 1.0 | fit 0.5, kept | **filtered** (`OUT_OF_AREA`) |

Filtering only when both locations are known avoids hiding Circles because of missing data. An unknown
location scores 0.5, a neutral midpoint: it is no evidence that the Circle is far away. This matters for
the planted scenario: **6 Speak Up Circle** is `in_person` with an unknown leader location, and the README
expects it to be recommended to user 7.

## 7. Near-duplicate Circles

Pairwise similarity over all 780 Circle pairs:

- **Descriptions are templated**: token-shingle Jaccard is 1.00 for *every* same-topic pair and up to 0.71
  for different-topic pairs. Description similarity only restates the topic.
- **Tags are random noise**: the planted duplicates 10/11/12 have tag-and-topic Jaccard 0.20–0.25, lower
  than the non-duplicate pair 20/22 (0.50).
- **Name similarity alone over-matches across topics**: 5 "Women Who Lead" vs 12 "Negotiate Like a Leader"
  share the stem `lead`.

Rule used: two Circles are near-duplicates when they share the **same primary topic** and their **normalised
name tokens** (lowercase, `&` → `and`, stopwords and generic group nouns such as *circle, collective, table,
lab, room, guild* removed, light suffix stemming) have an **overlap coefficient of 1.0**, meaning one name's
distinctive words are contained in the other's. Clusters are connected components.

| Threshold | Clusters produced |
| --- | --- |
| overlap 1.0 (chosen) | **{10, 11, 12}** Negotiation, {13, 37} Confident Voices / The Confidence Lab |
| overlap 0.5 | the above plus {6, 38} Speak…, {15, 40} Network…, {16, 39} Mentor… |

The stricter threshold is used. Pairs like "Speak Up Circle" and "Speak With Impact" are different groups on
the same topic; the per-topic cap of 2 already limits that kind of redundancy.

## 8. Evaluation scenario records

| Scenario | User | Evidence | Expected handling |
| --- | --- | --- | --- |
| Cold start | **42** Zoe | No interests, no memberships, completeness 0, no location, joined 1 day before reference time. Only such user. | `cold_start`: active, open, virtual/hybrid first, one per topic. |
| Obvious matches | **7** Priya, Seattle | Interests `leadership-skills`, `public-speaking`; member of 4 only. | **5 Women Who Lead** (hybrid, leader in Seattle, 11 posts, 7 seats) and **6 Speak Up Circle** (in-person, 8 posts, 4 seats) in the top 3. 1 and 38 are in-person in New York and Boston, so filtered. |
| Duplicates | **15** Nadia, Chicago | Interests `negotiation`, `confidence`; member of 9 and 35. | At most one of 10/11/12. 12 is in-person in Denver (filtered); 10 or 11 survives as the cluster representative. |
| Full / inactive | **23** Grace, Atlanta | Interest `getting-promoted`; member of 23 only. | 20 filtered `FULL`; 21 filtered `INACTIVE` (and unlisted); **22 Level Up Collective** recommended (hybrid, 8 posts, 6 seats). |

Other full Circles: none. Other inactive Circles: 32 The Resilience Room.

## 9. Things the data does not support

| Instruction | What the data has | Handling |
| --- | --- | --- |
| Network affiliation signal (weight 0.10) | No networks in any file | Signal dropped; no `networks` / `user_networks` tables. Weight moved to topic (+0.05) and room to join (+0.10), with profile affinity lowered to 0.10. |
| In-person "same city" check | No Circle location | Leader location as a proxy (section 6). |
| Dedupe on tags and description shingles | Tags random, descriptions templated | Topic plus name similarity (section 7). |
| Profile affinity on company industry | No Circle industry field | Industry not used; bio and job-title keywords map to topics through a small lexicon. |
| Cover image as a tie-breaker | Missing on some of the most active Circles | Not used. |
| Membership tenure | Timestamps inconsistent | Not used. |

## 10. Additional observations

- `access = unlisted` (18, 21, 30) usually means a Circle is hidden from discovery. 30 Early Career Collective
  is large and very active and would otherwise rank highly in cold start. Decision: hard-filter unlisted
  Circles with reason code `UNLISTED`.
- User 18 leads Circle 12 and has no stated interests. Without extra handling she would be recommended
  Circles 10 and 11, near-duplicates of the Circle she already runs. Decision: filter Circles in the same
  dedupe cluster as any Circle the member already belongs to (`SAME_AS_JOINED`).
- Circles 27 and 28 have no topic, description or tags; their names suggest regional or affinity groups.
  They are never matched on topic, and diversification treats all topic-less Circles as one bucket so they
  cannot crowd a list.
