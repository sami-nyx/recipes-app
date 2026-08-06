FROM python:3.11-slim

WORKDIR /app

# Cache dependencies layer
COPY test/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bake application & test code
COPY . .

ENTRYPOINT ["pytest"]
CMD ["test/backend/recipes-api-test"]