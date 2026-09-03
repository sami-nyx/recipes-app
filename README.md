# Recipes Platform — CI/CD & GitOps Portfolio Project


## Overview

**Recipes Platform** is a full-stack application built primarily as a portfolio project for demonstrating a production-style **CI/CD and GitOps workflow using GitHub Actions and Argo CD**.

The application itself consists of:

* An **Angular** frontend
* A **Flask REST API**
* **SQLAlchemy** for database access
* A **PostgreSQL** database

Users can create accounts, authenticate, create and manage recipes, and browse recipes published by other users.

While the application demonstrates full-stack development, the main focus of this repository is the automation surrounding it:

* Pull request validation (static analysis, unit tests, component tests)
* Path-based change detection, so unrelated components aren't rebuilt or retested
* Integration testing against the real system topology (nginx + API + database)
* Docker image builds with layer caching
* Semantic versioning and automated Git tagging
* Amazon ECR publishing, verified before promotion
* AWS authentication using GitHub OIDC — no long-lived credentials anywhere
* A self-refreshing automated promotion PR from `develop` to `main`
* Separate delivery paths for backend (GitOps → Kubernetes) and frontend (S3 + CloudFront)
* Slack pipeline notifications throughout

---

# CI/CD Architecture

The project uses **GitHub Actions** for CI and **Argo CD** for CD. Code is validated in progressively larger stages before an artifact is allowed to progress toward deployment, and the backend and frontend are promoted independently once they reach `main`.

```text
                         Developer
                             │
                             │ Push Feature
                             ▼
                     ┌────────────────┐
                     │ Feature Branch │
                     └───────┬────────┘
                             │
                             │ Pull Request
                             ▼
                       ┌───────────┐
                       │  develop  │◄──────────────────────┐
                       └─────┬─────┘                       │
                             │                              │
              ┌──────────────┼──────────────┐               │
              ▼              ▼              ▼               │
      Static Analysis   Unit Tests    Component Test        │
      (Super-Linter)   (Backend/UI)   (fast, no nginx)       │
              │              │              │               │
              └──────────────┴──────────────┘               │
                             │                                │
                    Push merges to develop                    │
                             │                                │
                             ▼                                │
                     Integration Test                          │
              (full stack: nginx + API + UI build + DB)         │
                             │                                  │
                    ┌────────┴────────┐                         │
                    ▼                 ▼                         │
             Backend changed?   Publish to ECR                  │
                    │            + Tag Git Commit                │
                    ▼                                             │
        Automated PR: develop → main ─────────────────────────────┘
        (created once, refreshed on every later push)
                             │
                             ▼
                           main
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        Backend changed?            Frontend changed?
                │                         │
                ▼                         ▼
       Update recipes-gitops      Build + deploy to
       repo (image tag) ──►         S3 + CloudFront
       Argo CD reconciles
       the EKS cluster
```

---

# Pull Request Pipeline

Pull requests targeting `develop` are validated with three independent, parallel checks - none of them wait on each other, so feedback arrives as fast as the slowest single check rather than the sum of all of them.

```text
PR → develop
      │
      ├──────────────► Slack: Pipeline Started
      │
      ├──────────────► Lint (Super-Linter)
      │
      ├──────────────► Unit Tests (backend and/or frontend, path-gated)
      │
      └──────────────► Component Test (recipes-api + postgres, always runs)
                              │
                              ▼
                       Pipeline Result
                              │
                              ▼
                       Slack Notification
```

Component Test is deliberately **not** the full integration tier - it validates `recipes-api` against its own direct dependency (PostgreSQL) only, with no nginx and no UI build in the loop. That keeps PR feedback fast. The full system (nginx routing, the built Angular app, everything talking to everything) is validated once per merge instead - see [Integration Testing](#integration-testing) below.

## Static Analysis

The pipeline uses **Super-Linter**, scoped to only the files this PR actually changed (`VALIDATE_ALL_CODEBASE: false`, diffed against the PR's real base branch).

Current validation includes:

* Python — Flake8
* Dockerfiles — Hadolint
* YAML — yamllint
* GitHub Actions — actionlint
* Bash — ShellCheck

This catches issues in application code, Dockerfiles, shell scripts, and workflow definitions themselves before any test tier runs.

---

# Path-Based Change Detection

Every pipeline needs to answer one question first: *what actually changed?* A shared reusable workflow, `detect-changes.yaml`, answers it once and every other workflow reads the result instead of re-deriving it:

```text
detect-changes.yaml
        │
        ▼
┌─────────────────────────────┐
│  backend      recipes-backend/recipes-api/**            │
│  frontend     recipes-ui/**                              │
│  integration  docker-compose.yaml, nginx/**,              │
│               test/component/**, the component/           │
│               integration-test workflows, .github/actions/** │
└─────────────────────────────┘
```

Both `unit-tests.yaml` (PR and push validation) and `push-to-main-ci.yaml` (production deploy) call this same workflow, so the path patterns only exist in one place. Downstream, this drives real skip-gating rather than just labeling:

* Backend unit tests only run when `recipes-backend/recipes-api/**` changed.
* Frontend unit tests only run when `recipes-ui/**` changed.
* The integration tier (see below) runs on *any* of the three categories changing, since it's the only place nginx routing and the UI build get exercised together - but only *publishes* a new backend image when the backend itself changed.
* On `main`, updating GitOps and deploying the UI are gated on backend/frontend independently, so a frontend-only release doesn't touch the Kubernetes side at all, and vice versa.

---

# Unit Testing

Two independent suites, each gated on its own path and run through reusable workflows so the same tests can be called from multiple pipelines without duplicating their definitions.

**Backend** (`unittest`, path-gated on `recipes-backend/recipes-api/**`):

* User registration
* Authentication
* Invalid credentials
* Recipe operations
* Protected API routes
* Input validation

**Frontend** (Angular's Vitest-based unit-test builder, path-gated on `recipes-ui/**`):

* Component creation and rendering
* Reactive form validation (e.g. login credential requirements)
* Conditional UI state (signed-in vs. guest navigation)

```text
.github/workflows/

├── detect-changes.yaml
├── unit-tests.yaml
├── component-test.yaml
├── integration-test.yaml
├── pr-to-develop-ci.yaml
├── push-to-develop-ci.yaml
└── push-to-main-ci.yaml
```

---

# Component Testing

Runs on every pull request. Validates `recipes-api` against its own direct dependency only:

```text
┌─────────────────┐
│ Component Test  │
│    Container     │
└────────┬────────┘
         │ HTTP, direct
         ▼
┌─────────────────┐
│    Flask API    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
└─────────────────┘
```

No nginx, no frontend build - this tier answers "does the API's own logic work," fast enough to run on every PR without slowing feedback down.

---

# Integration Testing

Runs once per merge to `develop` (not once per PR *and* once per merge - see [CI/CD Design Goals](#cicd-design-goals)). Brings up the real system topology through Docker Compose and routes requests through it exactly the way a browser would:

```text
┌─────────────────┐
│ Integration     │
│ Test Container  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐        ┌──────────────────┐
│     NGINX       │◄───────┤ recipes-ui-build  │
└────────┬────────┘        │ (one-shot: builds │
         │                 │  the Angular app  │
         ▼                 │  into a shared     │
┌─────────────────┐        │  volume, then      │
│    Flask API    │        │  exits)            │
└────────┬────────┘        └──────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
└─────────────────┘
```

The same `test/component/` pytest suite the component tier uses runs again here, unchanged - only its target moves from talking to `recipes-api` directly to talking through nginx, so proxying and routing become part of what's actually tested, not just assumed to work.

**nginx here is a local/CI convenience, not a production stand-in.** It gives `docker compose up` a single origin serving both the built UI and `/api` (avoiding CORS in local dev) and gives the test suite something to actually route through. Production doesn't use this container or this nginx config at all - see [GitOps & Production Delivery](#gitops--production-delivery).

---

# Docker Image Build

The Flask API is packaged as a Docker image using a multi-stage Dockerfile: a builder stage installs Python dependencies into an isolated prefix, and the runtime stage copies only that prefix plus the application code, running as a non-root user.

```text
Source Code
     │
     ▼
Docker Buildx
     │
     ├── Builder Stage
     │     └── Python dependencies
     │
     ▼
Runtime Stage
     │
     ├── Application code
     ├── Runtime libraries (version-pinned)
     └── Non-root user
```

The locally built image is loaded into the GitHub Actions runner and used directly during integration testing - it is **not rebuilt after testing**:

```text
Build Image
     │
     ▼
Integration Test
     │
     ▼
Tests Pass
     │
     ▼
Tag Same Image
     │
     ▼
Push to ECR
```

This ensures the artifact published to the registry is the exact artifact that passed integration testing, not a coincidentally-similar rebuild.

The Angular UI has its own Dockerfile too, but it's build-only - it never runs as a service. Its job is to produce the production build as a cacheable layer, which a compose service then copies into the volume nginx serves (see [Integration Testing](#integration-testing)). The pytest test-runner image (`test/component/`) is shared unchanged between the component and integration tiers.

---

# Docker Build Cache

Docker BuildKit caching is integrated with the GitHub Actions cache backend. Each image has its own cache scope, so editing one component doesn't invalidate another's cached layers:

```text
recipes-api        → GHA Cache Scope: recipes-api
recipes-ui          → GHA Cache Scope: recipes-ui
component-test       → GHA Cache Scope: component-test
integration-test       → GHA Cache Scope: integration-test
```

This significantly reduces rebuild time when dependency layers haven't changed - a source-only edit reuses the cached `pip install`/`npm ci` layer rather than reinstalling from scratch.

---

# AWS Authentication with OIDC

The CI pipeline does not require long-lived AWS access keys. GitHub Actions authenticates to AWS using **OpenID Connect (OIDC)**.

```text
GitHub Actions
      │
      │ OIDC Token
      ▼
   AWS STS
      │
      │ AssumeRole
      ▼
GitHub Actions IAM Role
      │
      ▼
 Amazon ECR / S3 / CloudFront
```

The workflow requires:

```yaml
permissions:
  contents: read
  id-token: write
```

AWS IAM then controls exactly what each role is authorized to do - the ECR-push role and the S3-push role are separate, scoped independently.

This eliminates the need to store permanent AWS access keys as repository secrets.

---

# Amazon ECR Publishing

After the integration tier passes **and** the push actually changed the backend, the image is tagged with a semantic version and published to **Amazon Elastic Container Registry**. A frontend-only or infra-only push runs the integration tier too (routing still needs validating) but publishes nothing - there's no new backend image to push.

```text
recipes-api (local)
       │
       │ docker tag
       ▼
ECR Repository
       │
       └── v1.4.8
```

The image is then verified using the AWS ECR API before the corresponding Git commit is tagged:

```text
docker push
    │
    ▼
Amazon ECR
    │
    ▼
aws ecr describe-images
    │
    ├── Image missing ──► Pipeline Failure
    │
    └── Image exists
             │
             ▼
         Git Tag
```

This creates a direct relationship between:

```text
Git Commit  ↔  Git Version Tag  ↔  Docker Image Tag
```

---

# Frontend Deployment

The frontend has no image and no registry - it ships as a static production build, synced directly to S3 and served through CloudFront. This only runs on push to `main`, and only when `recipes-ui/**` actually changed:

```text
npm run build --configuration production
       │
       ▼
aws s3 sync --delete
       │        (tagged with the deploying commit's SHA
       │         as object metadata - not a git tag, since
       │         a frontend-only release mints none)
       ▼
S3 Static Hosting
       │
       ▼
CloudFront Invalidation
```

Unlike the backend, this path never touches GitOps or Kubernetes - S3 + CloudFront is the entire production surface for the UI.

---

# Semantic Versioning

Backend releases use semantic version tags:

```text
vMAJOR.MINOR.PATCH
```

Example:

```text
v1.4.7  →  v1.4.8
```

A custom GitHub composite action (`resolve-tag`) inspects repository tags and exposes:

```text
LATEST_TAG
NEXT_TAG
```

The next version is used when publishing a new Docker image, and again independently when promoting to `main` (the GitOps repository gets its own tag, tracking the app repo's tags but not identical to them).

---

# GitHub Composite Actions

Repeated CI/CD functionality is implemented using custom composite actions.

```text
.github/actions/
│
├── notify-slack/
│   └── action.yaml
│
├── resolve-tag/
│   └── action.yaml
│
└── push-to-ecr/
    └── action.yaml
```

## `resolve-tag`

Responsible for:

* Fetching Git tags
* Finding the latest semantic version (strict-regex validated, not just glob-matched)
* Calculating the next release version
* Bootstrapping to `v1.0.0` if no tags exist yet

Outputs:

```text
LATEST_TAG
NEXT_TAG
```

## `push-to-ecr`

Responsible for:

* AWS OIDC authentication
* Amazon ECR authentication
* Tagging the tested local Docker image
* Pushing the image
* Returning the published image URI

## `notify-slack`

Provides standardized CI/CD notifications for:

* Pipeline started
* Pipeline succeeded
* Pipeline failed
* Release promotion

---

# Development Promotion Pipeline

A push to `develop` runs unit tests, then the integration tier, then - if a new backend image was published - verifies and tags it, then opens or refreshes the promotion PR toward `main`:

```text
Push → develop
       │
       ▼
   Unit Tests (path-gated)
       │
       ▼
 Integration Test  (backend, frontend, or infra changed)
       │
       ├── Backend changed? ──► Resolve Version ──► Push to ECR ──► Verify ──► Tag Git Commit
       │
       ▼
 Create or Refresh PR
 develop ─────────────► main
```

Promotion to `main` happens only after the development pipeline succeeds - and only when there's actually something to promote (a push that touches none of backend/frontend/integration opens no PR at all).

---

# Automated Pull Requests

Once the development pipeline succeeds, GitHub Actions automatically creates - or refreshes - a pull request:

```text
develop
   │
   │ Automated Pull Request
   ▼
 main
```

Before creating another PR, the workflow checks whether an open `develop → main` pull request already exists. If one does, and this push published a new backend image, its title and body are **refreshed** to the current tag rather than left stale - a PR opened for `v1.0.32` that sits open while `v1.0.33` merges shows `v1.0.33`, not a title quietly out of date with what it would actually ship if merged.

The release PR contains:

* What changed (backend, frontend, infra, or a combination)
* Image tag (or "unchanged" for a frontend/infra-only release)
* Source and target branch
* Commit SHA

---

# Slack Notifications

Pipeline status is reported to Slack through a reusable composite action.

Notifications are sent when pipelines:

* Start
* Succeed
* Fail
* Produce a release candidate
* Create a promotion pull request

Example flow:

```text
GitHub Push
      │
      ▼
🚀 Pipeline Started
      │
      ▼
Tests / Build / Publish
      │
      ├── Failure ─────► ❌ Slack Failure Notification
      │
      └── Success ─────► ✅ Slack Success Notification
```

Release notifications include branch, commit SHA, individual job results, and (when applicable) the Docker image version and release PR number/URL.

---

# GitOps & Production Delivery

Backend and frontend ship to production through entirely different paths, and neither one runs from this repository directly.

```text
                    push → main
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
   Backend changed?             Frontend changed?
           │                           │
           ▼                           ▼
  Resolve next version          npm run build (production)
           │                           │
           ▼                           ▼
  Commit new image tag to        aws s3 sync + CloudFront
  recipes-gitops repo            invalidation
  (separate repository)
           │
           ▼
  Argo CD detects the
  change and reconciles
  the AWS EKS cluster
```

The backend is deployed via **GitOps**: this repository's CI never talks to Kubernetes directly. It commits the new image tag into a separate `recipes-gitops` repository, and **Argo CD**, watching that repository (App-of-Apps pattern), reconciles the live cluster to match - certificate management, ingress routing, the PostgreSQL cluster (CloudNativePG), and secrets injection (External Secrets Operator) are all managed the same way, as Argo CD Applications sourced from that repo.

The frontend deliberately does **not** go through GitOps or Kubernetes at all - it's a static build synced straight to S3, fronted by CloudFront. There is no production nginx; the nginx in this repository's `docker-compose.yaml` is a local/CI-only detail (see [Integration Testing](#integration-testing)).

---

# Application Architecture

The workload used by the CI/CD platform is a recipe-sharing application.

```text
┌──────────────────────────────┐
│       Angular Frontend       │
│                              │
│ TypeScript / HTML / CSS      │
└──────────────┬───────────────┘
               │
               │ REST API
               ▼
┌──────────────────────────────┐
│        Flask Backend         │
│                              │
│ Authentication               │
│ Recipe API                   │
│ User API                     │
│ Health Endpoints             │
└──────────────┬───────────────┘
               │
               │ SQLAlchemy
               ▼
┌──────────────────────────────┐
│          PostgreSQL          │
└──────────────────────────────┘
```

---

# Application Features

Users can:

* Create an account
* Authenticate with the backend
* Create recipes
* Edit their recipes
* Delete their recipes
* Browse recipes created by other users, filterable by contributor
* View recipe authors

Recipes can contain:

* Title
* Description
* Preparation time
* Cooking time
* Servings
* Recipe parts
* Instructions
* Ingredients
* Cost information
* Nutrition information

---

# Technology Stack

| Area                     | Technology                            |
| ------------------------ | -------------------------------------- |
| Frontend                 | Angular                                |
| Frontend Language        | TypeScript                             |
| Frontend Testing         | Vitest (Angular's unit-test builder)   |
| Backend                  | Flask                                  |
| Backend Language         | Python                                 |
| ORM                      | SQLAlchemy                             |
| Database                 | PostgreSQL                             |
| Reverse Proxy (local/CI) | NGINX                                  |
| Containers               | Docker                                 |
| Integration Environment  | Docker Compose                         |
| CI/CD                    | GitHub Actions                         |
| Container Registry       | Amazon ECR                             |
| Frontend Hosting         | Amazon S3 + CloudFront                 |
| Production Orchestration | Kubernetes (AWS EKS)                   |
| Continuous Delivery      | Argo CD (GitOps)                       |
| Cloud Authentication     | GitHub OIDC + AWS IAM                  |
| Static Analysis          | Super-Linter                           |
| Versioning               | Semantic Versioning                    |
| Notifications            | Slack                                  |

---

# Repository Structure

```text
.
├── .github/
│   ├── actions/
│   │   ├── notify-slack/
│   │   ├── push-to-ecr/
│   │   └── resolve-tag/
│   │
│   └── workflows/
│       ├── detect-changes.yaml
│       ├── unit-tests.yaml
│       ├── component-test.yaml
│       ├── integration-test.yaml
│       ├── pr-to-develop-ci.yaml
│       ├── push-to-develop-ci.yaml
│       └── push-to-main-ci.yaml
│
├── recipes-backend/
│   └── recipes-api/
│
├── recipes-ui/
│
├── nginx/
│
├── test/
│   └── component/
│
├── docker-compose.yaml
│
└── README.md
```

---

# CI/CD Design Goals

The pipeline was designed around several principles.

### Build Once

The Docker image that passes integration testing is the same image pushed to the registry.

### Short-Lived Credentials

AWS authentication uses GitHub OIDC instead of permanent AWS access keys, scoped per-purpose (ECR push vs. S3 push are separate roles).

### Reusability

Reusable workflows and composite actions reduce duplicated CI/CD configuration - path-based change detection in particular exists in exactly one place (`detect-changes.yaml`) and is called by every workflow that needs it.

### Fast Feedback, Then Depth

PR validation stays cheap (component test only, no nginx, no UI build) so feedback arrives quickly; the full system is validated once per merge instead of once per PR *and* once per merge, without giving up integration coverage entirely.

### Fail Before Promotion

A release can progress only when required validation stages succeed, and only when there's actually something to promote - an unrelated push opens no promotion PR at all.

### Artifact Traceability

Application versions are linked across:

```text
Git Commit  ↔  Semantic Version  ↔  Docker Image  ↔  ECR Artifact
```

### Observability

Slack notifications provide visibility into pipeline execution and release promotion at every stage, not just success/failure at the end.

---

# Project Purpose

The Recipes Platform was built as a portfolio project to demonstrate practical experience designing and implementing a complete software delivery lifecycle - from a pull request to a change actually running in production.

The main areas demonstrated by the project are:

* GitHub Actions CI/CD design, including reusable workflows and composite actions
* Path-based change detection and skip-gating across a multi-component monorepo
* A tiered testing strategy (component vs. full integration) balancing feedback speed against coverage
* Static code analysis
* Automated unit, component, and integration testing
* Docker image creation and BuildKit layer caching
* Container artifact promotion, verified before it's trusted
* Semantic versioning and automated Git tagging
* AWS IAM and GitHub OIDC federation - no long-lived cloud credentials
* Amazon ECR, S3, and CloudFront
* GitOps delivery to Kubernetes via Argo CD
* Automated, self-refreshing promotion pull requests
* Slack CI/CD notifications

The Angular and Flask application provides a realistic workload on which the CI/CD and deployment architecture can operate.

---

## Author

Built as a DevOps and CI/CD portfolio project around a full-stack Angular, Flask, PostgreSQL application.
