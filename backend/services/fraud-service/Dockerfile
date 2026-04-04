FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PORT=8000

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential curl \
	&& rm -rf /var/lib/apt/lists/*

RUN groupadd --system appgroup \
	&& useradd --system --gid appgroup --create-home appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["/app/docker-entrypoint.sh"]
