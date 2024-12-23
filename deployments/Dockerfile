FROM python:3.12-alpine

WORKDIR /code/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install uv

COPY uv.lock pyproject.toml /code/
RUN uv sync --frozen --no-install-project

COPY . /code/

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "app.main"]
