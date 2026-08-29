# ============================================================
# Stage 1 - Builder
# ============================================================

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# No apt packages needed here: every dependency in requirements.txt ships
# a prebuilt wheel for this platform (psycopg2-binary included), so there's
# nothing for a C compiler or libpq headers to build.

COPY requirements.txt .

# Install dependencies into a separate prefix
RUN pip install \
    --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


# ============================================================
# Stage 2 - Runtime
# ============================================================

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime library required by psycopg/PostgreSQL clients. curl was here
# too, but nothing in this image actually uses it - the compose-level
# healthcheck calls Python's urllib directly, and production's
# readinessProbe/livenessProbe are Kubernetes httpGet probes (kubelet
# makes the request itself, from outside the container) - confirmed
# against recipes-cluster-resources/apps/recipes-api/templates/
# deployment.yaml before removing it.
#
# Version pinned per hadolint DL3008 (reproducible builds) - resolved via
# `apt-cache policy libpq5` against this same base image. Will need
# bumping if/when python:3.11-slim's Debian snapshot moves past this
# version and it ages out of the apt mirror.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=17.11-0+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Run as a non-root user
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000
CMD ["sh", "-c", "exec gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    'app:create_app()'"]