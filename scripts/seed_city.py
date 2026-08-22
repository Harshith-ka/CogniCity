"""Standalone city seeder — run to populate the database."""

import asyncio

from backend.app.core.database import engine, async_session, Base
from backend.app.engine.city_generator import generate_city


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        stats = await generate_city(db, population=200, seed=42)
        print(f"City generated: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
