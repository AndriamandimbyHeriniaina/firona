"""Legal source policy: the only gate before a collector may run.

Example:
    from apps.sources.policy import CollectionDenied, assert_can_collect
    try:
        assert_can_collect(source)
    except CollectionDenied:
        return
"""

from __future__ import annotations

from collections.abc import Iterable

from apps.sources.models import Source


class CollectionDenied(Exception):
    """Raised when a Source must not be contacted (inactive, no consent, or kind not enabled)."""


# v3 HTTP collectors may only target these kinds. Others can be stored, not fetched.
COLLECTABLE_KINDS = frozenset(
    {
        Source.Kind.META_ADS,
        Source.Kind.GOOGLE_TRENDS,
    }
)

CONSENT_REQUIRED_KINDS = frozenset(
    {
        Source.Kind.FACEBOOK_PAGE,
        Source.Kind.FACEBOOK_GROUP,
        Source.Kind.MARKETPLACE_PARTNER,
    }
)


def assert_can_collect(source: Source) -> None:
    """Raise CollectionDenied unless this source is allowed to be fetched.

    Example:
        assert_can_collect(source)
        client.fetch(source.external_id)
    """
    reason = source.block_reason
    if reason:
        raise CollectionDenied(reason)


def collectable_sources() -> Iterable[Source]:
    """Yield sources that pass the legal gate (no HTTP)."""
    for source in Source.objects.all():
        if source.can_collect:
            yield source
