# recipes-ui

The Angular frontend for the Recipes Platform - authentication, browsing/searching recipes, and a full recipe editor with dynamic parts/ingredients/instructions.

---

## Pages

| Route | Component | What it does |
|---|---|---|
| `/` | `Landing` | Entry page |
| `/explore` | `Explore` | Browse/filter recipes - search, prep time, contributor, "only my recipes" |
| `/recipes/:id` | `ViewRecipeComponent` | A single recipe's full detail |
| `/recipes/create`, `/recipes/:id/edit` | `RecipeFormComponent` | Create/edit a recipe - reactive form, dynamic `FormArray`s for parts, ingredients, and instructions |
| `/user/:authorId` | `UserBioComponent` | An author's public profile + their published recipes |
| `/login`, `/register` | `LoginComponent`, `RegisterComponent` | Auth |

---

## Tech Stack

- **Framework:** Angular 22 (standalone components, no `NgModule`s), TypeScript
- **UI:** Angular Material
- **Forms:** Reactive Forms (`FormBuilder`/`FormGroup`/`FormArray`)
- **Testing:** Vitest (Angular's `ng test` builder), against `jsdom`
- **State:** Angular signals - no external state management library

---

## Talking to the API

`src/environments/environment.ts` / `environment.production.ts` hold `apiUrl` - everything goes through `environment.fullApiUrl`, never a hardcoded host. `auth.interceptor.ts` is registered globally and attaches `Authorization: Bearer <token>` to every outgoing request once `UserService` holds a token from login - no per-service auth header wiring.

---

## Project Structure

```text
src/app/
├── components/
│   ├── landing/                     # Entry page
│   ├── explore/                     # Recipe browsing + search/filter
│   ├── recipe-card/                 # Reusable recipe summary card
│   ├── recipe-filter/                # Search/filter controls used by explore
│   ├── recipe-form-component/        # Create/edit - dynamic parts/ingredients/instructions
│   ├── view-recipe-component/        # Single recipe detail view
│   ├── user-bio-component/           # Author profile page
│   ├── personal-component/           # Current user's own recipe list
│   ├── edit-profile-dialog/          # Profile-edit Material dialog
│   ├── login-component/, register-component/
│   └── auth/                        # auth.interceptor.ts
├── services/
│   ├── user-service.ts              # Auth state, token storage, current user
│   ├── recipe.service.ts            # Recipe CRUD against the API
│   └── author-data.service.ts       # Author-profile lookups
├── models/                          # Recipe, Author, RecipeFilter, etc.
├── environments/                    # apiUrl per build configuration
└── app.routes.ts
```

---

## Commands

```bash
npm ci                                       # install dependencies
npm run start                                # dev server, http://localhost:4200
npm run build -- --configuration production  # production build (what CI runs)
npm run test                                 # unit tests (Vitest, watch off in CI: --watch=false)
```
