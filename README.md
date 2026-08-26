# Recipes Platform — CI/CD & GitOps Portfolio Project


## Overview

**Recipes Platform** is a full-stack application built primarily as a portfolio project for demonstrating a production-style **CI/CD workflow using GitHub Actions**.

The application itself consists of:

* An **Angular** frontend
* A **Flask REST API**
* **SQLAlchemy** for database access
* A **PostgreSQL** database

Users can create accounts, authenticate, create and manage recipes, and browse recipes published by other users.

While the application demonstrates full-stack development, the main focus of this repository is the automation surrounding it:

* Pull request validation
* Static code analysis
* Unit testing
* Integration testing
* Docker image builds
* Docker build caching
* Semantic versioning
* Amazon ECR publishing
* AWS authentication using GitHub OIDC
* Automated Git tagging
* Automated promotion between branches
* Slack pipeline notifications

---

# CI/CD Architecture

The project uses **GitHub Actions** as its CI/CD orchestration platform.

The pipeline is separated into multiple stages so that code is validated before an artifact is allowed to progress toward deployment.

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
                       │  develop  │
                       └─────┬─────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
         Static Validation            Unit Tests
         Super-Linter                 Backend/UI
                │                         │
                └────────────┬────────────┘
                             ▼
                      Integration Tests
                             │
                             ▼
                    Docker Image Build
                             │
                             ▼
                    Push Image to ECR
                             │
                             ▼
                      Verify ECR Image
                             │
                             ▼
                     Create Git Version
                             │
                             ▼
                    Automated PR to main
                             │
                             ▼
                           main
                             │
                             ▼
                       GitOps Delivery
```

---

# Pull Request Pipeline

Pull requests targeting `develop` are validated before they can be promoted.

The workflow performs several independent checks.

```text
PR → develop
      │
      ├──────────────► Slack: Pipeline Started
      │
      ├──────────────► Static Linting
      │
      └──────────────► Unit Tests
                              │
                              ▼
                     Integration Tests
                              │
                              ▼
                    Pipeline Result
                              │
                              ▼
                       Slack Notification
```

## Static Analysis

The pipeline uses **Super-Linter** to validate repository files.

Current validation includes:

* Python — Flake8
* Dockerfiles — Hadolint
* YAML — yamllint
* GitHub Actions — actionlint
* Bash — ShellCheck

This allows issues in application code, Dockerfiles, shell scripts, and workflow definitions to be detected before integration testing begins.

---

# Unit Testing

Unit tests are executed using reusable GitHub Actions workflows.

The backend test suite validates application behavior such as:

* User registration
* Authentication
* Invalid credentials
* Recipe operations
* Protected API routes
* Input validation

Reusable workflows allow the same tests to be executed from multiple pipelines without duplicating workflow definitions.

```text
.github/workflows/

├── unit-tests.yaml
├── integration-tests.yaml
├── pr-to-develop-ci.yaml
├── push-to-develop-ci.yaml
└── push-to-main-ci.yaml
```

---

# Integration Testing

Integration tests run the application in an isolated Docker Compose environment.

The test environment contains:

```text
┌─────────────────┐
│ Integration     │
│ Test Container  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│     NGINX       │
└────────┬────────┘
         │
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

The tests validate the behavior of the application using real network communication between containers instead of mocking the entire backend stack.

This provides confidence that the Docker image being promoted behaves correctly when connected to its required infrastructure.

---

# Docker Image Build

The Flask API is packaged as a Docker image using a multi-stage Dockerfile.

GitHub Actions uses Docker Buildx to build the application image.

```text
Source Code
     │
     ▼
Docker Buildx
     │
     ├── Builder Stage
     │     ├── Python dependencies
     │     └── Build dependencies
     │
     ▼
Runtime Stage
     │
     ├── Application code
     ├── Runtime libraries
     └── Non-root user
     │
     ▼
recipes-api:test
```

The locally built image is loaded into the GitHub Actions runner and used directly during integration testing.

The important result is that the pipeline does **not rebuild the application after testing**.

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

This ensures that the artifact published to the registry is the exact artifact that passed integration testing.

---

# Docker Build Cache

Docker BuildKit caching is integrated with the GitHub Actions cache backend.

Each image uses its own cache scope.

For example:

```text
recipes-api
     │
     └── GHA Cache Scope: recipes-api

integration-tests
     │
     └── GHA Cache Scope: integration-tests
```

This significantly reduces rebuild time when dependency layers have not changed.

Typical cached layers include:

* Base image processing
* Operating system packages
* Python dependency installation
* Build stages

---

# AWS Authentication with OIDC

The CI pipeline does not require long-lived AWS access keys.

GitHub Actions authenticates to AWS using **OpenID Connect (OIDC)**.

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
 Amazon ECR
```

The workflow requires:

```yaml
permissions:
  contents: read
  id-token: write
```

AWS IAM then controls exactly what operations the GitHub Actions role is authorized to perform.

This eliminates the need to store permanent AWS access keys as repository secrets.

---

# Amazon ECR Publishing

After successful integration testing, the application image is tagged with a semantic version and published to **Amazon Elastic Container Registry**.

Example:

```text
recipes-api:test
       │
       │ docker tag
       ▼
ECR Repository
       │
       └── v1.4.8
```

The image is then verified using the AWS ECR API before the corresponding Git commit is tagged.

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
Git Commit
    ↕
Git Version Tag
    ↕
Docker Image Tag
```

---

# Semantic Versioning

Application releases use semantic version tags:

```text
vMAJOR.MINOR.PATCH
```

Example:

```text
v1.4.7
   │
   ▼
v1.4.8
```

A custom GitHub composite action inspects repository tags and exposes:

```text
LATEST_TAG
NEXT_TAG
```

The next version is used when publishing a new Docker image.

---

# GitHub Composite Actions

Repeated CI/CD functionality is implemented using custom composite actions.

```text
.github/actions/
│
├── notify-slack/
│   └── action.yaml
│
├── resolve-next-tag/
│   └── action.yaml
│
└── push-to-ecr/
    └── action.yaml
```

## `resolve-next-tag`

Responsible for:

* Fetching Git tags
* Finding the latest semantic version
* Validating tag format
* Calculating the next release version

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

A successful push to the development branch triggers the release pipeline.

```text
Push → develop
       │
       ▼
   Unit Tests
       │
       ▼
Integration Tests
       │
       ▼
 Build Docker Image
       │
       ▼
 Resolve Version
       │
       ▼
 Push Image to ECR
       │
       ▼
 Verify ECR Image
       │
       ▼
 Tag Git Commit
       │
       ▼
 Create PR
 develop ─────────────► main
```

This means promotion to `main` occurs only after the application artifact has passed the development CI pipeline.

---

# Automated Pull Requests

Once the development pipeline succeeds, GitHub Actions automatically creates a pull request:

```text
develop
   │
   │ Automated Pull Request
   ▼
 main
```

Before creating another PR, the workflow checks whether an open `develop → main` pull request already exists.

This prevents duplicate promotion pull requests.

The release PR contains information such as:

* Semantic version
* Source branch
* Target branch
* Commit SHA
* Pipeline status

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

Release notifications can include:

```text
Branch
Commit SHA
Test results
Docker image version
Pull request number
Pull request URL
```

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
* Browse recipes created by other users
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

| Area                    | Technology            |
| ----------------------- | --------------------- |
| Frontend                | Angular               |
| Frontend Language       | TypeScript            |
| Backend                 | Flask                 |
| Backend Language        | Python                |
| ORM                     | SQLAlchemy            |
| Database                | PostgreSQL            |
| Reverse Proxy           | NGINX                 |
| Containers              | Docker                |
| Integration Environment | Docker Compose        |
| CI/CD                   | GitHub Actions        |
| Container Registry      | Amazon ECR            |
| Cloud Authentication    | GitHub OIDC + AWS IAM |
| Static Analysis         | Super-Linter          |
| Versioning              | Semantic Versioning   |
| Notifications           | Slack                 |

---

# Repository Structure

```text
.
├── .github/
│   ├── actions/
│   │   ├── notify-slack/
│   │   ├── push-to-ecr/
│   │   └── resolve-next-tag/
│   │
│   └── workflows/
│       ├── integration-tests.yaml
│       ├── unit-tests.yaml
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

AWS authentication uses GitHub OIDC instead of permanent AWS access keys.

### Reusability

Reusable workflows and composite actions reduce duplicated CI/CD configuration.

### Fail Before Promotion

A release can progress only when required validation stages succeed.

### Artifact Traceability

Application versions are linked across:

```text
Git Commit
    ↕
Semantic Version
    ↕
Docker Image
    ↕
ECR Artifact
```

### Observability

Slack notifications provide visibility into pipeline execution and release promotion.

---

# Project Purpose

The Recipes Platform was built as a portfolio project to demonstrate practical experience designing and implementing a complete software delivery lifecycle.

The main areas demonstrated by the project are:

* GitHub Actions CI/CD design
* Reusable workflows
* Composite GitHub Actions
* Branch-based promotion
* Static code analysis
* Automated unit and integration testing
* Docker image creation
* BuildKit caching
* Container artifact promotion
* Semantic versioning
* AWS IAM
* GitHub OIDC federation
* Amazon ECR
* Automated Git tagging
* Automated pull requests
* Slack CI/CD notifications

The Angular and Flask application provides a realistic workload on which the CI/CD and deployment architecture can operate.

---

## Author

Built as a DevOps and CI/CD portfolio project around a full-stack Angular, Flask, PostgreSQL application.
