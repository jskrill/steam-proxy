FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV HOST "0.0.0.0"
ENV PORT "8080"
ENV GUNICORN_CMD_ARGS "--capture-output -b $HOST -p $PORT -k uvicorn.workers.UvicornWorker"

WORKDIR /opt/app

RUN mkdir -p /opt/app

COPY main.py pyproject.toml uv.lock /opt/app/.

RUN uv sync --locked

CMD ["uv", "run", "gunicorn", "main:app"]
