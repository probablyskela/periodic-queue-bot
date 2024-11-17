from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.chat import ChatRepository
from app.repository.entry import EntryRepository
from app.repository.event import EventRepository
from app.repository.occurrence import OccurrenceRepository


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

        self.chat = ChatRepository(session=session)
        self.event = EventRepository(session=session)
        self.occurrence = OccurrenceRepository(session=session)
        self.entry = EntryRepository(session=session)
