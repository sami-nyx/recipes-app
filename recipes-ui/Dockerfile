# Build-only image: this never runs as a long-lived service. Its job is
# to produce /app/dist/recipes-ui/browser as a cacheable Docker layer -
# docker-compose.yaml then copies that output into a shared volume
# (rendered_spa_content) that nginx mounts read-only, keeping nginx
# itself a generic, stock image that doesn't know or care how the UI
# was built.
FROM node:24-alpine

WORKDIR /app

# package.json/package-lock.json first, installed before the rest of the
# source is copied in - `npm ci` only re-runs when the lockfile actually
# changes; editing application code alone reuses this layer.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Same command push-to-main-ci.yaml's deploy-ui job runs for the real S3
# deploy - what's built here matches what actually ships, not a
# coincidentally-similar dev build.
RUN npm run build -- --configuration production
