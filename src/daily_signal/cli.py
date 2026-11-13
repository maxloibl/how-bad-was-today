"""Command-line entry points for Daily Signal.

The ``seed-sources`` subcommand loads the rights-locked source configuration and
seeds any missing sources, publisher groups, feeds, and permission revisions
into the configured database in a single transaction. It prints a JSON summary
and exits 0 on success, or 2 when the configuration is malformed or attempts to
grant rights.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from daily_signal.core.config import Settings, get_settings
from daily_signal.infrastructure.db.seed import (
    SeedSummary,
    SourceConfigError,
    SourcesConfig,
    load_sources_config,
    seed_sources,
)
from daily_signal.infrastructure.db.session import create_engine, create_session_factory


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="daily-signal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed = subparsers.add_parser(
        "seed-sources", help="Seed rights-locked news sources into the database"
    )
    seed.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to sources.yaml (defaults to settings.sources_config_path)",
    )
    return parser


async def _run_seed(settings: Settings, config: SourcesConfig) -> SeedSummary:
    """Run the seed against ``settings`` in a single transaction."""
    engine = create_engine(settings)
    try:
        factory = create_session_factory(engine)
        async with factory() as session, session.begin():
            return await seed_sources(session, config)
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the requested subcommand."""
    args = build_parser().parse_args(argv)

    if args.command != "seed-sources":
        build_parser().print_help()
        return 0

    settings = get_settings()
    config_path = args.config if args.config is not None else settings.sources_config_path

    try:
        config = load_sources_config(config_path)
    except SourceConfigError as exc:
        print(f"seed-sources: {exc}", file=sys.stderr)
        return 2

    summary = asyncio.run(_run_seed(settings, config))
    print(json.dumps({"created": summary.created, "skipped": summary.skipped}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
