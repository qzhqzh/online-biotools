# syntax=docker/dockerfile:1

FROM node:22-bookworm AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build:docker

FROM ensemblorg/ensembl-vep:release_116.0

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/biotools && \
    /opt/biotools/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY manage.py /app/manage.py
COPY config /app/config
COPY apps /app/apps
COPY reference-manifest.yaml /app/reference-manifest.yaml
COPY --from=frontend /frontend/dist /app/apps/portal/static/portal/dist

ENV PATH="/opt/biotools/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VEP_BIN=/opt/vep/src/ensembl-vep/vep \
    VEP_CACHE_DIR=/data/vep \
    VEP_ASSEMBLY=GRCh37 \
    DJANGO_DEBUG=0 \
    DJANGO_ALLOWED_HOSTS=*

RUN mkdir -p /data/vep /data/tmp && \
    useradd --create-home --uid 10001 biotools && \
    chown -R biotools:biotools /app /data

USER biotools

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "320"]
