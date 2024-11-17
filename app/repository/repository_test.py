from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_database(db_session: AsyncSession) -> None:
    await db_session.execute(select(text("1")))
