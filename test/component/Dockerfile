FROM python:3.11-slim

WORKDIR /app

# Cache dependencies layer
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake application & test code
COPY . .

# Run as a non-root user, matching recipes-api's own Dockerfile - nothing
# here needs root, and this container talks to other services over the
# network only (no privileged operations, no host mounts to write to).
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["pytest"]
CMD ["."]