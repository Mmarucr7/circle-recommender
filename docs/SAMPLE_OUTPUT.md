# Sample output

Produced by `make evaluate` against the seed dataset (reference time 2026-09-21T00:00:00+00:00).
Top 5 recommendations per member; every member in the dataset is checked.

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| Cold start: strategy is cold_start with a full list | PASS | strategy=cold_start, results=10 |
| Cold start: results span distinct topics and are all active | PASS | 10 distinct topics across 10 results |
| Obvious matches: #5 and #6 are both in the top 3 | PASS | top 3 = [5, 6, 35] |
| Duplicates: exactly one of #10/#11/#12 is returned | PASS | returned [11] |
| Full / inactive: #20 and #21 are excluded, #22 ranks first | PASS | results = [22, 2, 16, 19, 13, 27, 39, 15, 11, 5] |
| No full Circle is ever returned | PASS | 100 members checked |
| No inactive Circle is ever returned | PASS | 100 members checked |
| No unlisted Circle is ever returned | PASS | 100 members checked |
| No Circle the member already belongs to | PASS | 100 members checked |
| No in-person Circle outside the member's area | PASS | 100 members checked |
| No two results share a dedupe cluster | PASS | 100 members checked |
| Every member gets a non-empty list | PASS | 100 members checked |
| Explanations are at most 140 characters | PASS | 100 members checked |

## Scenario members

### User 42: Cold start

interests: none · location: not set or remote · member of 0 Circles · strategy: `cold_start`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #27 Women of the 405 | virtual | An active virtual Circle where members posted 20 times this month, a great place to start. |
| 2 | #39 Mentorship Matters | virtual | An active virtual Circle on sponsorship & mentorship where members posted 11 times this month, a great place to start. |
| 3 | #11 The Negotiation Table | hybrid | An active hybrid Circle on negotiation where members posted 13 times this month, a great place to start. |
| 4 | #5 Women Who Lead | hybrid | An active hybrid Circle on leadership skills where members posted 11 times this month, a great place to start. |
| 5 | #24 Burnout to Balance | hybrid | An active hybrid Circle on stress & burnout where members posted 10 times this month, a great place to start. |

### User 7: Obvious matches

interests: leadership-skills, public-speaking · location: Seattle · member of 1 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #5 Women Who Lead | hybrid | Matches your interest in leadership skills, and members posted 11 times this month. |
| 2 | #6 Speak Up Circle | in_person | Matches your interest in public speaking and leadership skills, and members posted 8 times this month. |
| 3 | #35 Board-Ready Women | in_person | Matches your interest in leadership skills, and meets near you in Seattle. |
| 4 | #14 Beyond Imposter Syndrome | hybrid | Also covers public speaking, which you're interested in, and members posted 5 times this month. |
| 5 | #39 Mentorship Matters | virtual | Meets online, so you can join from anywhere, and members posted 11 times this month. |

### User 15: Duplicate Circles

interests: confidence, negotiation · location: Chicago · member of 2 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #11 The Negotiation Table | hybrid | Matches your interest in negotiation, and members posted 13 times this month. |
| 2 | #37 The Confidence Lab | virtual | Matches your interest in confidence, and meets online, so you can join from anywhere. |
| 3 | #5 Women Who Lead | hybrid | Builds on leadership skills, a topic from Circles you're already in, and members posted 11 times this month. |
| 4 | #23 Allies at Work | virtual | Also covers negotiation, which you're interested in, and meets online, so you can join from anywhere. |
| 5 | #34 Visibility Lab | hybrid | Builds on visibility & recognition, a topic from Circles you're already in, and members posted 5 times this month. |

### User 23: Full / inactive

interests: getting-promoted · location: Atlanta · member of 1 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #22 Level Up Collective | hybrid | Matches your interest in getting promoted, and members posted 8 times this month. |
| 2 | #2 Next Chapter Circle | virtual | Meets online, so you can join from anywhere, and members posted 6 times this month. |
| 3 | #16 Mentors & Sponsors | virtual | Meets online, so you can join from anywhere, and members posted 6 times this month. |
| 4 | #19 Working Mothers United | in_person | Also covers getting promoted, which you're interested in, and members posted 9 times this month. |
| 5 | #13 Confident Voices | in_person | Meets near you in Atlanta, and members posted 14 times this month. |

## Other members

### User 4: No stated interests, profile mentions a career break

interests: none · location: New York · member of 2 Circles · strategy: `blended`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #2 Next Chapter Circle | virtual | Meets online, so you can join from anywhere, and members posted 6 times this month. |
| 2 | #31 Team Leads Circle | in_person | Meets near you in New York, and members posted 10 times this month. |
| 3 | #27 Women of the 405 | virtual | Meets online, so you can join from anywhere, and members posted 20 times this month. |
| 4 | #39 Mentorship Matters | virtual | Meets online, so you can join from anywhere, and members posted 11 times this month. |
| 5 | #1 The Elevation Circle | in_person | Meets near you in New York, and members posted 15 times this month. |

### User 18: No stated interests; leads a Negotiation Circle

interests: none · location: Denver · member of 5 Circles · strategy: `blended`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #39 Mentorship Matters | virtual | Meets online, so you can join from anywhere, and members posted 11 times this month. |
| 2 | #4 Women in Transition | virtual | Meets online, so you can join from anywhere, and members posted 6 times this month. |
| 3 | #27 Women of the 405 | virtual | Meets online, so you can join from anywhere, and members posted 20 times this month. |
| 4 | #5 Women Who Lead | hybrid | Meets both online and in person, and members posted 11 times this month. |
| 5 | #23 Allies at Work | virtual | Meets online, so you can join from anywhere, and welcomes new members to join right away. |

### User 52: Three stated interests, remote

interests: communication, getting-promoted, work-life-integration · location: not set or remote · member of 9 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #25 Clear Communicators | virtual | Matches your interest in communication and work-life integration, and meets online, so you can join from anywhere. |
| 2 | #3 The Balance Collective | in_person | Matches your interest in work-life integration, and members posted 20 times this month. |
| 3 | #39 Mentorship Matters | virtual | Also covers communication, which you're interested in, and members posted 11 times this month. |
| 4 | #13 Confident Voices | in_person | Builds on confidence, a topic from Circles you're already in, and members posted 14 times this month. |
| 5 | #24 Burnout to Balance | hybrid | Also covers work-life integration, which you're interested in, and members posted 10 times this month. |

### User 79: Joined 3 weeks ago

interests: being-the-only-one, managing-a-team · location: not set or remote · member of 4 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #31 Team Leads Circle | in_person | Matches your interest in managing a team, and members posted 10 times this month. |
| 2 | #36 First 90 Days | virtual | Matches your interest in managing a team, and members posted 5 times this month. |
| 3 | #5 Women Who Lead | hybrid | Builds on leadership skills, a topic from Circles you're already in, and members posted 11 times this month. |
| 4 | #22 Level Up Collective | hybrid | Builds on getting promoted, a topic from Circles you're already in, and members posted 8 times this month. |
| 5 | #1 The Elevation Circle | in_person | Builds on leadership skills, a topic from Circles you're already in, and members posted 15 times this month. |

### User 100: One stated interest, Boston

interests: career-breaks · location: Boston · member of 3 Circles · strategy: `personalized`

| # | Circle | Format | Explanation |
| --- | --- | --- | --- |
| 1 | #33 Return & Rise | hybrid | Matches your interest in career breaks, and members posted 5 times this month. |
| 2 | #5 Women Who Lead | hybrid | Builds on leadership skills, a topic from Circles you're already in, and members posted 11 times this month. |
| 3 | #6 Speak Up Circle | in_person | Also covers career breaks, which you're interested in, and members posted 8 times this month. |
| 4 | #22 Level Up Collective | hybrid | Builds on getting promoted, a topic from Circles you're already in, and members posted 8 times this month. |
| 5 | #16 Mentors & Sponsors | virtual | Meets online, so you can join from anywhere, and members posted 6 times this month. |
