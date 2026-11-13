"""Rights-locked source seed loading and database seeding.

The seed configuration (``config/sources.yaml``) is the single point where
sources and their permission defaults are described. Because a mis-edited
config could otherwise grant publishing rights to a source that is still under
review, :func:`load_sources_config` deliberately rejects any configuration that
grants rights: every source must be ``in_review``, ``enabled=false`` and
``permissions_approved=false``, and every permission default must be ``false``
apart from ``review_status``.

Seeding is idempotent and non-destructive. Rows are looked up by their natural
keys (slug, ``feed_url``, ``(source_id, revision)``) and only created when
absent; an existing source's ``enabled``, ``review_status`` and permission
flags are never modified. UUIDs are application-generated with deterministic
UUIDv5 values so reruns produce the same identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daily_signal.infrastructure.db.models import (
    NewsSource,
    PublisherGroup,
    SourceFeed,
    SourcePermission,
)

#: Boolean permission flags carried by a permission record. These are the
#: fields that the rights lock requires to be ``false``.
_PERMISSION_FLAGS: tuple[str, ...] = (
    "fetch_metadata",
    "fetch_full_text",
    "analyze_content",
    "store_temporary",
    "store_long_term",
    "send_to_external_llm",
    "create_embeddings",
    "create_adaptations",
    "republish_original_content",
    "publish_derivatives",
    "republish_media",
)


class SourceConfigError(ValueError):
    """Raised when a sources configuration is malformed or grants rights."""


class PermissionDefaults(BaseModel):
    """Default permission flags applied to a source's first permission revision."""

    model_config = ConfigDict(extra="forbid")

    review_status: str = "in_review"
    fetch_metadata: bool = False
    fetch_full_text: bool = False
    analyze_content: bool = False
    store_temporary: bool = False
    store_long_term: bool = False
    send_to_external_llm: bool = False
    create_embeddings: bool = False
    create_adaptations: bool = False
    republish_original_content: bool = False
    publish_derivatives: bool = False
    republish_media: bool = False


class SourceConfig(BaseModel):
    """A single news source and its approval state as described in YAML."""

    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str
    publisher_group_id: str
    publisher_group_name: str
    homepage_url: str
    origin_country: str
    primary_language: str
    source_type: str
    license_code: str
    license_url: str
    terms_url: str
    content_scope: str
    attribution_requirements: str
    feed_url: str
    review_status: str
    enabled: bool
    permissions_approved: bool


class SourcesConfig(BaseModel):
    """The parsed ``sources.yaml`` document."""

    model_config = ConfigDict(extra="forbid")

    version: int
    sources: tuple[SourceConfig, ...]
    permission_defaults: PermissionDefaults


@dataclass(frozen=True)
class SeedSummary:
    """Outcome of a seed run: how many sources were created vs. skipped."""

    created: int
    skipped: int


def stable_uuid(kind: str, key: str) -> UUID:
    """Return a deterministic UUIDv5 for ``(kind, key)``.

    Namespaced under the URL namespace with a ``daily-signal`` prefix so seed
    identifiers are stable across environments and reruns.
    """
    return uuid5(NAMESPACE_URL, f"daily-signal:{kind}:{key}")


def load_sources_config(path: str | Path) -> SourcesConfig:
    """Load and validate a sources configuration, rejecting rights grants.

    Raises :class:`SourceConfigError` unless the document is ``version: 1``,
    every source is ``in_review``/``enabled=false``/``permissions_approved=false``,
    and every permission default is ``false`` apart from ``review_status``.
    """
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SourceConfigError(f"cannot read sources config {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise SourceConfigError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise SourceConfigError(f"{path}: expected a top-level YAML mapping")

    try:
        config = SourcesConfig.model_validate(raw)
    except ValidationError as exc:
        raise SourceConfigError(f"{path}: {exc}") from exc

    _enforce_rights_lock(config)
    return config


def _enforce_rights_lock(config: SourcesConfig) -> None:
    """Fail closed on any configuration that would grant rights."""
    if config.version != 1:
        raise SourceConfigError("sources config version must be 1")

    defaults = config.permission_defaults
    if defaults.review_status != "in_review":
        raise SourceConfigError("permission_defaults.review_status must be 'in_review'")
    for flag in _PERMISSION_FLAGS:
        if getattr(defaults, flag) is not False:
            raise SourceConfigError(f"permission_defaults.{flag} must be false")

    for source in config.sources:
        if source.review_status != "in_review":
            raise SourceConfigError(f"source '{source.slug}' review_status must be 'in_review'")
        if source.enabled is not False:
            raise SourceConfigError(f"source '{source.slug}' enabled must be false")
        if source.permissions_approved is not False:
            raise SourceConfigError(f"source '{source.slug}' permissions_approved must be false")


async def seed_sources(session: AsyncSession, config: SourcesConfig) -> SeedSummary:
    """Insert missing sources and their dependents, never altering existing rows.

    Returns a summary counting sources created this run versus sources that were
    already present (and therefore left untouched).
    """
    created = 0
    skipped = 0

    for source_cfg in config.sources:
        publisher_group_id = await _ensure_publisher_group(session, source_cfg)

        source = await session.scalar(select(NewsSource).where(NewsSource.slug == source_cfg.slug))
        if source is None:
            source = NewsSource(
                id=stable_uuid("source", source_cfg.slug),
                publisher_group_id=publisher_group_id,
                slug=source_cfg.slug,
                name=source_cfg.name,
                homepage_url=source_cfg.homepage_url,
                source_type=source_cfg.source_type,
                origin_country=source_cfg.origin_country,
                primary_language=source_cfg.primary_language,
                review_status="in_review",
                enabled=False,
            )
            session.add(source)
            await session.flush()
            created += 1
        else:
            skipped += 1

        await _ensure_feed(session, source, source_cfg)
        await _ensure_permission(session, source, source_cfg, config.permission_defaults)

    return SeedSummary(created=created, skipped=skipped)


async def _ensure_publisher_group(session: AsyncSession, source_cfg: SourceConfig) -> UUID:
    """Return the publisher group id, creating the group by slug when absent."""
    slug = source_cfg.publisher_group_id
    group = await session.scalar(select(PublisherGroup).where(PublisherGroup.slug == slug))
    if group is None:
        group = PublisherGroup(
            id=stable_uuid("publisher-group", slug),
            slug=slug,
            name=source_cfg.publisher_group_name,
            country_code=source_cfg.origin_country,
        )
        session.add(group)
        await session.flush()
    return group.id


async def _ensure_feed(session: AsyncSession, source: NewsSource, source_cfg: SourceConfig) -> None:
    """Create the source's feed by ``feed_url`` when absent."""
    feed = await session.scalar(
        select(SourceFeed).where(SourceFeed.feed_url == source_cfg.feed_url)
    )
    if feed is None:
        session.add(
            SourceFeed(
                id=stable_uuid("feed", source_cfg.slug),
                source_id=source.id,
                feed_url=source_cfg.feed_url,
                feed_kind="rss",
                enabled=False,
            )
        )


async def _ensure_permission(
    session: AsyncSession,
    source: NewsSource,
    source_cfg: SourceConfig,
    defaults: PermissionDefaults,
) -> None:
    """Create revision 1 of the source permission when absent, all flags false."""
    permission = await session.scalar(
        select(SourcePermission).where(
            SourcePermission.source_id == source.id,
            SourcePermission.revision == 1,
        )
    )
    if permission is None:
        session.add(
            SourcePermission(
                id=stable_uuid("permission", source_cfg.slug),
                source_id=source.id,
                revision=1,
                review_status="in_review",
                license_code=source_cfg.license_code,
                license_url=source_cfg.license_url,
                terms_url=source_cfg.terms_url,
                content_scope=source_cfg.content_scope,
                attribution_requirements=source_cfg.attribution_requirements,
                fetch_metadata=defaults.fetch_metadata,
                fetch_full_text=defaults.fetch_full_text,
                analyze_content=defaults.analyze_content,
                store_temporary=defaults.store_temporary,
                store_long_term=defaults.store_long_term,
                send_to_external_llm=defaults.send_to_external_llm,
                create_embeddings=defaults.create_embeddings,
                create_adaptations=defaults.create_adaptations,
                republish_original_content=defaults.republish_original_content,
                publish_derivatives=defaults.publish_derivatives,
                republish_media=defaults.republish_media,
            )
        )
