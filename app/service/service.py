import typing
import uuid
from datetime import datetime

import numexpr
import pytz

from app import schema
from app.config import config
from app.repository import Repository
from app.util import RelativeDelta


class Service:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    async def load_configuration(
        self,
        chat_id: int,
        configuration: schema.ConfigurationInput,
        configuration_raw: dict[str, typing.Any],
    ) -> None:
        from app import tasks

        await self._repository.delete_chat_events(chat_id=chat_id)

        chat = schema.Chat(
            id=chat_id,
            timezone=configuration.timezone,
            config=configuration_raw,
        )

        await self._repository.upsert_chat(chat=chat)

        events = []

        for event_input in configuration.events:
            event = schema.Event(
                chat_id=chat_id,
                name=event_input.name,
                description=event_input.description,
                initial_date=event_input.initial_date,
                next_date=event_input.initial_date,
                periodicity=event_input.periodicity,
                offset=event_input.offset,
                times_occurred=event_input.times_occurred,
            )

            event = self.update_event_next_date(event=event)
            if event is None:
                continue

            tasks.send_event_notification_message_task.apply_async(
                kwargs={"event_id": str(event.id)},
                eta=event.next_date - self.evaluate_event_offset(event=event),
            )

            events.append(event)

        await self._repository.upsert_events(events=events)

    async def get_chat(self, chat_id: int) -> schema.Chat | None:
        return await self._repository.get_chat(chat_id=chat_id)

    async def upsert_events(self, events: list[schema.Event]) -> None:
        await self._repository.upsert_events(events=events)

    async def get_event(self, event_id: uuid.UUID) -> schema.Event | None:
        return await self._repository.get_event(event_id=event_id)

    async def insert_occurrence(self, occurrence: schema.Occurrence) -> None:
        await self._repository.insert_occurrence(occurrence=occurrence)

    async def get_occurrence(self, occurrence_id: uuid.UUID) -> schema.Occurrence | None:
        return await self._repository.get_occurrence(occurrence_id=occurrence_id)

    async def upsert_entry(self, entry: schema.Entry) -> None:
        await self._repository.upsert_entry(entry=entry)

    async def get_entry(self, occurrence_id: uuid.UUID, user_id: int) -> schema.Entry | None:
        return await self._repository.get_entry(occurrence_id=occurrence_id, user_id=user_id)

    async def get_entries(self, occurrence_id: uuid.UUID) -> list[schema.Entry]:
        return await self._repository.get_entries(occurrence_id=occurrence_id)

    async def delete_last_user_entry(self, occurence_id: uuid.UUID, user_id: int) -> None:
        await self._repository.delete_last_user_entry(occurence_id=occurence_id, user_id=user_id)

    def update_event_next_date(self, event: schema.Event) -> schema.Event | None:
        """Update event's `next_date` to be the closest possible occurrence date.

        Returns `None` if an event will never occur again
        (E.g. if `periodicity` is `None` and `next_date` already passed)
        """
        ts = datetime.now(tz=pytz.utc) + RelativeDelta(minutes=1)

        if event.next_date > ts + self.evaluate_event_offset(event=event):
            return event

        if not event.periodicity:
            return None

        while event.next_date <= ts + self.evaluate_event_offset(event=event):
            event.next_date += self.evaluate_event_periodicity(event=event)
            event.times_occurred += 1

        return event

    def evaluate_event_periodicity(self, event: schema.Event) -> RelativeDelta:
        """Evaluate `util.RelativeDelta` object for next event occurrance.

        If event has no periodicity rules specified, minimal allowed periodicity returned.

        Returns `util.RelativeDelta` object.
        """
        if not event.periodicity:
            return config.min_periodicity
        return max(
            config.min_periodicity,
            self.evaluate_period(period=event.periodicity, t=event.times_occurred),
        )

    def evaluate_event_offset(self, event: schema.Event) -> RelativeDelta:
        """Evaluate offset for `next_date`.

        If event has no offset rules specified, empty offset returned (0 seconds).

        Returns `util.RelativeDelta` object.
        """
        if not event.offset:
            return RelativeDelta()
        return self.evaluate_period(period=event.offset, t=event.times_occurred)

    @staticmethod
    def evaluate_period(period: schema.Period, t: int) -> RelativeDelta:
        """Evaluate `schema.Period` object with `t` and `n` variables. Where `n = t + 1`.

        Returns `util.RelativeDelta` object.
        """

        def evaluate(ex: str | None) -> int:
            if ex is None:
                return 0
            return round(numexpr.evaluate(ex, {"t": t, "n": t + 1}, {}).item())

        return RelativeDelta(**{key: evaluate(value) for key, value in period.model_dump().items()})
