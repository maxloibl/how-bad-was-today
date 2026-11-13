"""Publication rights checks for source permissions and item-level exceptions."""

from dataclasses import dataclass

from daily_signal.domain.enums import ContentBasis, ReviewStatus


class RightsError(ValueError):
    """Raised when the recorded rights do not permit an intended use."""


@dataclass(frozen=True)
class PermissionProfile:
    """Publication-relevant flags of an approved source permission."""

    review_status: ReviewStatus
    analyze_content: bool
    create_adaptations: bool
    publish_derivatives: bool
    send_to_external_llm: bool
    fetch_full_text: bool


@dataclass(frozen=True)
class ItemRights:
    """Item-level rights that may override the source permission defaults."""

    license_verified: bool
    contains_third_party_material: bool


def assert_can_publish(
    permission: PermissionProfile,
    item: ItemRights,
    content_basis: ContentBasis,
    *,
    uses_external_llm: bool = False,
    uses_full_text: bool = False,
) -> None:
    """Raise :class:`RightsError` unless publishing is permitted."""
    if permission.review_status != ReviewStatus.APPROVED:
        raise RightsError("source permission must be approved before publishing")
    if not item.license_verified:
        raise RightsError("item license must be verified")
    if item.contains_third_party_material:
        raise RightsError("item contains third-party material and may not be published")
    if not permission.publish_derivatives:
        raise RightsError("permission does not allow publishing derivatives")
    if not permission.analyze_content:
        raise RightsError("permission does not allow analyzing content")
    if content_basis == ContentBasis.ADAPTATION and not permission.create_adaptations:
        raise RightsError("permission does not allow creating adaptations")
    if uses_external_llm and not permission.send_to_external_llm:
        raise RightsError("permission does not allow sending content to an external LLM")
    if uses_full_text and not permission.fetch_full_text:
        raise RightsError("permission does not allow fetching full text")
