FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY cases ./cases
COPY docs ./docs
COPY harness ./harness
COPY tests ./tests

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e .

CMD ["harness-demo", "compare", "--scenario", "incident-response"]
