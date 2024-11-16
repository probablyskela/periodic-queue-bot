import typing

from pydantic import BaseModel, Field, ValidationInfo
from pydantic.functional_validators import AfterValidator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.util import RelativeDelta


class PostgresConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int
    path: str


class RabbitMQConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int


def build_database_url(_: str, info: ValidationInfo) -> str:
    postgres: PostgresConfig = info.data["postgres"]
    database_url = MultiHostUrl.build(
        scheme="postgresql+asyncpg",
        username=postgres.username,
        password=postgres.password,
        host=postgres.host,
        port=postgres.port,
        path=postgres.path,
    )
    return str(database_url)


def build_rabbitmq_url(_: str, info: ValidationInfo) -> str:
    rabbitmq: RabbitMQConfig = info.data["rabbitmq"]
    rabbitmq_url = MultiHostUrl.build(
        scheme="amqp",
        username=rabbitmq.username,
        password=rabbitmq.password,
        host=rabbitmq.host,
        port=rabbitmq.port,
    )
    return str(rabbitmq_url)


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    token: str = Field(default=...)

    date_format: str = "%d-%m-%Y %H:%M:%S %z"

    min_periodicity: RelativeDelta = RelativeDelta(minutes=1)
    max_periodicity: RelativeDelta = RelativeDelta(years=2)

    min_offset: RelativeDelta = RelativeDelta()
    max_offset: RelativeDelta = RelativeDelta(years=2)

    postgres: PostgresConfig = Field(default=...)
    database_url: typing.Annotated[str, AfterValidator(build_database_url)] = ""

    rabbitmq: RabbitMQConfig = Field(default=...)
    rabbitmq_url: typing.Annotated[str, AfterValidator(build_rabbitmq_url)] = ""


config = Config()
