from collections.abc import Sequence

from circle_recommender.recommender.features import is_out_of_area
from circle_recommender.recommender.models import Circle, FilteredCircle, FilterReason, Member


def filter_reasons(member: Member, circle: Circle) -> tuple[FilterReason, ...]:
    checks = (
        (circle.id in member.joined_circle_ids, FilterReason.ALREADY_MEMBER),
        (
            circle.id not in member.joined_circle_ids and circle.cluster_id in member.joined_cluster_ids,
            FilterReason.SAME_AS_JOINED,
        ),
        (circle.is_full, FilterReason.FULL),
        (not circle.is_active, FilterReason.INACTIVE),
        (not circle.is_public, FilterReason.UNLISTED),
        (is_out_of_area(member, circle), FilterReason.OUT_OF_AREA),
    )
    return tuple(reason for failed, reason in checks if failed)


def split_eligible(member: Member, circles: Sequence[Circle]) -> tuple[list[Circle], list[FilteredCircle]]:
    eligible: list[Circle] = []
    filtered: list[FilteredCircle] = []
    for circle in sorted(circles, key=lambda c: c.id):
        reasons = filter_reasons(member, circle)
        if reasons:
            filtered.append(FilteredCircle(circle.id, reasons))
        else:
            eligible.append(circle)
    return eligible, filtered
