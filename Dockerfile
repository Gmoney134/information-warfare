FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==2.3.2

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root

COPY src/ ./src/
COPY disinfodomains.csv ./

RUN poetry install --only main

EXPOSE 8000

CMD ["poetry", "run", "start"]
