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

# NOT --configuration production: that swaps in environment.production.ts,
# which points at the real deployed API (https://www.weaversls.com) -
# correct for the actual S3/CloudFront deploy, where frontend and backend
# are genuinely on different origins, but wrong here. This build only ever
# runs inside docker-compose.yaml's stack, where nginx is the single local
# origin for both the UI and /api (see that file's top comment) - a build
# that calls the real production API instead would silently bypass the
# local recipes-api container entirely, defeating the point of that stack
# and, worse, being a "local" UI that's actually live against production
# data. --configuration development uses environment.development.ts
# (http://localhost:80/api), which is exactly this stack's own origin.
RUN npm run build -- --configuration development
