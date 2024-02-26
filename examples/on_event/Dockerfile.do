FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y build-essential git
WORKDIR /app
COPY examples/on_event/requirements.txt .
RUN python -m venv /app/venv
RUN . /app/venv/bin/activate && pip install -r requirements.txt


FROM python:3.12-slim
COPY --from=builder /app/venv /app/venv
WORKDIR /app
COPY . /app
ENV PATH="/app/venv/bin:$PATH"
ENTRYPOINT ["python", "examples/on_event/do.py"]