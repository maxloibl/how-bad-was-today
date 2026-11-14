"""Command-line entry points for Daily Signal.

The ``seed-sources`` subcommand loads the rights-locked source configuration and
seeds any missing sources, publisher groups, feeds, and permission revisions
into the configured database in a single transaction. It prints a JSON summary
and exits 0 on success, or 2 when the configuration is malformed or attempts to
grant rights.

The ``worker`` and ``scheduler`` subcommands run the background process loops in
the foreground, installing SIGINT/SIGTERM handlers so the container stops
cleanly (with a Windows fallback for the proactor event loop). Both share this
codebase and image with the API but run as separate processes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from daily_signal.core.config import Settings, get_settings
from daily_signal.core.logging import configure_logging
from daily_signal.infrastructure.db.seed import (
    SeedSummary,
    SourceConfigError,
    SourcesConfig,
    load_sources_config,
    seed_sources,
)
from daily_signal.infrastructure.db.session import create_engine, create_session_factory
from daily_signal.jobs.scheduler import run_scheduler
from daily_signal.jobs.worker import run_worker

#: A long-running process loop, e.g. :func:`run_worker` or :func:`run_scheduler`.
ProcessRunner = Callable[[Settings, asyncio.Event], Awaitable[None]]


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
    subparsers.add_parser("worker", help="Run the background worker heartbeat loop")
    subparsers.add_parser("scheduler", help="Run the daily analysis scheduler loop")
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


async def _run_process(runner: ProcessRunner, settings: Settings) -> None:
    """Configure logging, wire signal handling, and run a process loop."""
    configure_logging(settings.log_level)
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)
    await runner(settings, stop_event)


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    """Request a clean shutdown on SIGINT/SIGTERM.

    ``loop.add_signal_handler`` is not implemented on Windows' proactor event
    loop, so fall back to :mod:`signal` handlers that wake the loop in a
    thread-safe way. ``stop_event`` is set at most once either way.
    """
    loop = asyncio.get_running_loop()

    def _stop(_signum: int, _frame: object) -> None:
        loop.call_soon_threadsafe(stop_event.set)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            signal.signal(sig, _stop)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the requested subcommand."""
    args = build_parser().parse_args(argv)

    if args.command == "seed-sources":
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

    if args.command in {"worker", "scheduler"}:
        settings = get_settings()
        runner: ProcessRunner = run_worker if args.command == "worker" else run_scheduler
        asyncio.run(_run_process(runner, settings))
        return 0

    build_parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
