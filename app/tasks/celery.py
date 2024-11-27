import asyncio
import typing

from celery import Celery, Task

from app.config import config


class AsyncTask(Task):
    """Allow running `async` celery tasks natively."""

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:  # noqa: ANN401
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))


celery = Celery(broker=config.rabbitmq_url, task_cls=AsyncTask)

celery.conf.event_serializer = "pickle"
celery.conf.task_serializer = "pickle"
celery.conf.result_serializer = "pickle"
celery.conf.accept_content = ["application/json", "application/x-python-serialize"]
