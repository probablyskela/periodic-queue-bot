FROM python:3.12-alpine

WORKDIR /code/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

RUN pip install uv

COPY uv.lock pyproject.toml /code/
RUN uv sync

COPY . /code/

CMD ["python", "-m", "app.main"]
