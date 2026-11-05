import sqlite3
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from circle_recommender import config
from circle_recommender.db import queries
from circle_recommender.db.connection import read_only_connection
from circle_recommender.recommender.features import is_out_of_area
from circle_recommender.recommender.models import Circle, Member, Strategy
from circle_recommender.services.recommendations import RecommendationRun, recommend_for_user

OUTPUT_PATH = config.PROJECT_ROOT / "docs" / "SAMPLE_OUTPUT.md"
TOP_N = 5
COLD_START_USER = 42
OBVIOUS_USER, OBVIOUS_CIRCLES = 7, frozenset({5, 6})
DUPLICATE_USER, DUPLICATE_CLUSTER = 15, frozenset({10, 11, 12})
FULL_INACTIVE_USER, FULL_CIRCLE, INACTIVE_CIRCLE, HEALTHY_ALTERNATIVE = 23, 20, 21, 22
SCENARIOS = {
    COLD_START_USER: "Cold start",
    OBVIOUS_USER: "Obvious matches",
    DUPLICATE_USER: "Duplicate Circles",
    FULL_INACTIVE_USER: "Full / inactive",
}
SAMPLE_USERS = {
    4: "No stated interests, profile mentions a career break",
    18: "No stated interests; leads a Negotiation Circle",
    52: "Three stated interests, remote",
    79: "Joined 3 weeks ago",
    100: "One stated interest, Boston",
}


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class Context:
    runs: dict[int, RecommendationRun]
    members: dict[int, Member]
    circles: dict[int, Circle]


def ids(run: RecommendationRun, top: int | None = None) -> list[int]:
    return [item.circle.id for item in run.result.items[:top]]


def every_user(context: Context, predicate: Callable[[int, RecommendationRun], list[int]]) -> list[str]:
    return [f"user {u}: {bad}" for u, run in context.runs.items() if (bad := predicate(u, run))]


def invariant_checks(context: Context) -> list[Check]:
    circles = context.circles
    rules: dict[str, Callable[[int, RecommendationRun], list[int]]] = {
        "No full Circle is ever returned": lambda _, r: [c for c in ids(r) if circles[c].is_full],
        "No inactive Circle is ever returned": lambda _, r: [c for c in ids(r) if not circles[c].is_active],
        "No unlisted Circle is ever returned": lambda _, r: [c for c in ids(r) if not circles[c].is_public],
        "No Circle the member already belongs to": lambda u, r: [
            c for c in ids(r) if c in context.members[u].joined_circle_ids
        ],
        "No in-person Circle outside the member's area": lambda u, r: [
            c for c in ids(r) if is_out_of_area(context.members[u], circles[c])
        ],
        "No two results share a dedupe cluster": lambda _, r: (
            [] if len({circles[c].cluster_id for c in ids(r)}) == len(ids(r)) else ids(r)
        ),
        "Every member gets a non-empty list": lambda _, r: [] if ids(r) else [0],
        "Explanations are at most 140 characters": lambda _, r: [
            i.circle.id for i in r.result.items if len(i.explanation) > config.EXPLANATION_MAX_CHARS
        ],
    }
    results = []
    for name, rule in rules.items():
        failures = every_user(context, rule)
        detail = f"{len(context.runs)} members checked" if not failures else "; ".join(failures[:5])
        results.append(Check(name, not failures, detail))
    return results


def scenario_checks(context: Context) -> list[Check]:
    cold = context.runs[COLD_START_USER]
    cold_topics = [context.circles[c].primary_topic for c in ids(cold)]
    obvious_top = set(ids(context.runs[OBVIOUS_USER], 3))
    duplicate_hits = [c for c in ids(context.runs[DUPLICATE_USER]) if c in DUPLICATE_CLUSTER]
    full_ids = ids(context.runs[FULL_INACTIVE_USER])
    return [
        Check(
            "Cold start: strategy is cold_start with a full list",
            cold.result.strategy is Strategy.COLD_START and len(cold_topics) == config.DEFAULT_LIMIT,
            f"strategy={cold.result.strategy.value}, results={len(cold_topics)}",
        ),
        Check(
            "Cold start: results span distinct topics and are all active",
            len(set(cold_topics)) == len(cold_topics)
            and all(context.circles[c].is_active for c in ids(cold)),
            f"{len(set(cold_topics))} distinct topics across {len(cold_topics)} results",
        ),
        Check(
            "Obvious matches: #5 and #6 are both in the top 3",
            obvious_top >= OBVIOUS_CIRCLES,
            f"top 3 = {sorted(obvious_top)}",
        ),
        Check(
            "Duplicates: exactly one of #10/#11/#12 is returned",
            len(duplicate_hits) == 1,
            f"returned {duplicate_hits}",
        ),
        Check(
            "Full / inactive: #20 and #21 are excluded, #22 ranks first",
            FULL_CIRCLE not in full_ids
            and INACTIVE_CIRCLE not in full_ids
            and full_ids[:1] == [HEALTHY_ALTERNATIVE],
            f"results = {full_ids}",
        ),
    ]


def run_all(connection: sqlite3.Connection) -> Context:
    user_ids = queries.fetch_user_ids(connection)
    runs = {u: recommend_for_user(connection, u, config.DEFAULT_LIMIT) for u in user_ids}
    members = {u: member for u in user_ids if (member := queries.fetch_member(connection, u))}
    circles = {c.id: c for c in queries.fetch_circles(connection, include_unavailable=True)}
    return Context(runs, members, circles)


def describe_member(member: Member) -> str:
    interests = ", ".join(member.stated_topics) or "none"
    location = member.location_label or "not set or remote"
    return (
        f"interests: {interests} · location: {location} · member of {len(member.joined_circle_ids)} Circles"
    )


def user_section(context: Context, user_id: int, title: str) -> list[str]:
    run = context.runs[user_id]
    lines = [
        f"### User {user_id}: {title}",
        "",
        f"{describe_member(context.members[user_id])} · strategy: `{run.result.strategy.value}`",
        "",
        "| # | Circle | Format | Explanation |",
        "| --- | --- | --- | --- |",
    ]
    for rank, item in enumerate(run.result.items[:TOP_N], start=1):
        circle = item.circle
        lines.append(f"| {rank} | #{circle.id} {circle.name} | {circle.format.value} | {item.explanation} |")
    return [*lines, ""]


def render(context: Context, checks: list[Check]) -> str:
    reference = next(iter(context.runs.values())).reference_time.isoformat()
    lines = [
        "# Sample output",
        "",
        f"Produced by `make evaluate` against the seed dataset (reference time {reference}).",
        f"Top {TOP_N} recommendations per member; every member in the dataset is checked.",
        "",
        "## Checks",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
        *[f"| {c.name} | {'PASS' if c.passed else 'FAIL'} | {c.detail} |" for c in checks],
        "",
        "## Scenario members",
        "",
    ]
    for user_id, title in SCENARIOS.items():
        lines += user_section(context, user_id, title)
    lines += ["## Other members", ""]
    for user_id, title in SAMPLE_USERS.items():
        lines += user_section(context, user_id, title)
    return "\n".join(lines).rstrip() + "\n"


def main(output: Path = OUTPUT_PATH) -> int:
    with read_only_connection(config.database_path()) as connection:
        context = run_all(connection)
    checks = scenario_checks(context) + invariant_checks(context)
    report = render(context, checks)
    output.write_text(report, encoding="utf-8")
    print(report)
    failed = [check.name for check in checks if not check.passed]
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed. Report written to {output}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
