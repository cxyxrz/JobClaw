import argparse
import asyncio

from .core.config import get_settings
from .core.logging import configure_logging
from .infra.db import dispose_db, get_sessionmaker, init_db
from .modules.auth.service import ensure_seed
from .modules.dicts.service import ensure_seed_dicts
from .modules.jobs.service import ensure_seed_jobs


async def _seed(with_data: bool) -> None:
    configure_logging(get_settings().log_json)
    init_db()
    async with get_sessionmaker()() as session:
        await ensure_seed(session)
        if with_data:
            dicts = await ensure_seed_dicts(session)
            jobs = await ensure_seed_jobs(session)
            print(f"seeded dict types: {dicts}, jobs: {jobs}")
        await session.commit()
    await dispose_db()
    print("seed done")


def main() -> None:
    parser = argparse.ArgumentParser(prog="jobclaw")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed", help="create seed users (dev only)")
    sub.add_parser(
        "seed-all", help="create seed users + dict types + sample jobs (dev only)"
    )
    args = parser.parse_args()
    if args.cmd == "seed":
        asyncio.run(_seed(with_data=False))
    elif args.cmd == "seed-all":
        asyncio.run(_seed(with_data=True))


if __name__ == "__main__":
    main()
