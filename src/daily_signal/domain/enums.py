"""Domain enums shared by the public contract and the persistence schema.

String values mirror ``contracts/openapi.yaml`` and
``docs/specs/daily-signal-v1.0/schema.sql`` exactly.
"""

from enum import StrEnum


class DayLabel(StrEnum):
    """Qualitative label attached to a 1-5 day score."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    MIXED = "mixed"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class Direction(StrEnum):
    """Editorial direction of a single story."""

    NEGATIVE = "negative"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    """Confidence of a published day score."""

    HIGH = "high"
    MEDIUM = "medium"
    LIMITED = "limited"


class Category(StrEnum):
    """Story category."""

    POLITICS = "politics"
    ECONOMY = "economy"
    WORLD = "world"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ENVIRONMENT = "environment"
    SOCIETY = "society"
    HEALTH = "health"


class Region(StrEnum):
    """Geographic region of a story."""

    GERMANY = "germany"
    EUROPE = "europe"
    WORLD = "world"


class ContentBasis(StrEnum):
    """Legal basis of the published story text."""

    FACTS_SYNTHESIS = "facts_synthesis"
    ADAPTATION = "adaptation"


class ReviewStatus(StrEnum):
    """Review lifecycle of a news source or its permission record."""

    CANDIDATE = "candidate"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class SourceType(StrEnum):
    """Editorial role of a news source."""

    EDITORIAL = "editorial"
    PRIMARY = "primary"
