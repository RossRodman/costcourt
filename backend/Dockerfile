# CostCourt API: FastAPI + LangGraph, served by uvicorn on port 8000.
#
#   docker build -t costcourt-backend backend
#   docker run -p 8000:8000 --env-file backend/.env costcourt-backend

FROM python:3.13-slim AS build
WORKDIR /src
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /venv
COPY pyproject.toml README.md ./
COPY app ./app
RUN /venv/bin/pip install .

FROM python:3.13-slim
ENV PATH=/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COSTCOURT_ENV=prod \
    COSTCOURT_HOST=0.0.0.0 \
    COSTCOURT_PORT=8000 \
    COSTCOURT_REPORTS_DIR=/data/reports
RUN useradd --system --uid 10001 --home-dir /app costcourt \
    && mkdir -p /app /data/reports \
    && chown -R costcourt /app /data
COPY --from=build /venv /venv
WORKDIR /app
USER costcourt
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
CMD ["costcourt", "--no-reload"]
