import pytest

from daily_signal.domain.enums import ContentBasis, ReviewStatus
from daily_signal.domain.licensing import (
    ItemRights,
    PermissionProfile,
    RightsError,
    assert_can_publish,
)

APPROVED = PermissionProfile(
    review_status=ReviewStatus.APPROVED,
    analyze_content=True,
    create_adaptations=True,
    publish_derivatives=True,
    send_to_external_llm=True,
    fetch_full_text=True,
)
CLEARED = ItemRights(license_verified=True, contains_third_party_material=False)


def test_approved_facts_synthesis_is_allowed() -> None:
    assert_can_publish(APPROVED, CLEARED, ContentBasis.FACTS_SYNTHESIS)


def test_in_review_source_is_rejected() -> None:
    profile = PermissionProfile(**{**APPROVED.__dict__, "review_status": ReviewStatus.IN_REVIEW})
    with pytest.raises(RightsError, match="approved"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS)


def test_unverified_or_third_party_item_is_rejected() -> None:
    with pytest.raises(RightsError, match="verified"):
        assert_can_publish(APPROVED, ItemRights(False, False), ContentBasis.FACTS_SYNTHESIS)
    with pytest.raises(RightsError, match="third-party"):
        assert_can_publish(APPROVED, ItemRights(True, True), ContentBasis.FACTS_SYNTHESIS)


def test_adaptation_requires_adaptation_permission() -> None:
    profile = PermissionProfile(**{**APPROVED.__dict__, "create_adaptations": False})
    with pytest.raises(RightsError, match="adaptation"):
        assert_can_publish(profile, CLEARED, ContentBasis.ADAPTATION)


def test_external_llm_and_full_text_require_their_flags() -> None:
    profile = PermissionProfile(
        **{
            **APPROVED.__dict__,
            "send_to_external_llm": False,
            "fetch_full_text": False,
        }
    )
    with pytest.raises(RightsError, match="external LLM"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS, uses_external_llm=True)
    with pytest.raises(RightsError, match="full text"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS, uses_full_text=True)
