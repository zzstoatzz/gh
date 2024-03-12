FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y build-essential git
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /app/venv
RUN . /app/venv/bin/activate && pip install -r requirements.txt --no-cache-dir

FROM python:3.12-slim
COPY --from=builder /app/venv /app/venv
WORKDIR /app
RUN mkdir /app/.prefect
COPY logging.yml .prefect/logging.yml
COPY do.py .
COPY tasks.py .
COPY handlers.py .prefect/handlers.py
ENV PATH="/app/venv/bin:$PATH"
ENV PREFECT_LOGGING_LEVEL=DEBUG
ENV PREFECT_EXPERIMENTAL_ENABLE_TASK_SCHEDULING=True