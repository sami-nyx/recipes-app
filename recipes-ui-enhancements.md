# recipes-ui enhancement plan

Restructuring plan for `recipes-ui` (Angular), mirroring the approach already used for
`recipes-backend/recipes-api` in `recipes-api-enhancements.md`. This first pass is scoped to
the services layer and the infrastructure around it (interceptor, guard) - components/
and models unrelated to services are out of scope here.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

## 1. Restructuring (services layer)

- [ ] **Rename `services/user-service.ts` → `services/user.service.ts`.** The only file in
  `services/` that doesn't follow the `*.service.ts` convention the other two already use
  (`recipe.service.ts`, `author-data.service.ts`). Pure rename, no behavior change.
- [ ] **Extract inline DTOs into `models/`.** `User`/`RegisterUserDto`/`AuthResponse` are
  currently declared inside `user-service.ts`; `AuthorData` is declared inside
  `author-data.service.ts`. Move them into `models/user.model.ts`, and reconcile `AuthorData`
  with the existing (near-duplicate) `models/author.model.ts` into one canonical `Author`
  shape. Also type `UserService.login()`'s `credentials: any` param as a proper
  `LoginCredentials` interface while touching this file. Pure type move + one type-safety
  fix, no runtime behavior change.
- [ ] **Merge `AuthorDataService` into `UserService`; delete `author-data.service.ts`.** Both
  services call `/api/users/...` for what's really one resource. `UserService` becomes the
  single owner of everything under `/api/users`: session signals (`currentUser`/`token`/
  `isAuthenticated`), `getAuthorById()` (moved in), and the two new methods below. Update the
  one call site that injects `AuthorDataService` today to inject `UserService` instead.
- [ ] **Move `auth.interceptor.ts` out of `components/auth/` into `core/interceptors/`.** It's
  not a component - it's cross-cutting HTTP infrastructure - so it shouldn't live under
  `components/`. Update the import in `app.config.ts`; delete the now-empty
  `components/auth/` directory.
- [ ] **Add `core/guards/auth.guard.ts`, apply it to `recipes/create` and `recipes/:id/edit`
  in `app.routes.ts`.** Neither route currently has a guard, so an unauthenticated user can
  navigate straight to either URL and hit a form that has nothing to actually submit
  against (every write endpoint requires a JWT server-side). A functional `CanActivateFn`
  (matching the functional-interceptor style already used) redirects to `/login` instead.
  This is a real behavior change, not a pure move - called out explicitly.
- [ ] **Standardize error handling across service methods.** Today it's ad hoc: `getRecipes()`
  swallows failures to `[]`, `getRecipeById()` swallows to `undefined`, `deleteRecipe()`
  catches and re-throws, `createRecipe()`/`updateRecipe()`/`getAuthorById()` don't catch at
  all. Apply one explicit policy: reads that back a cache/list may fail soft (empty/
  undefined, so a transient error doesn't crash a listing page); writes (create/update/
  delete) must always propagate so the calling component can show the user something went
  wrong. Add the missing `catchError`s so every method matches the policy instead of
  whatever it happened to be written as.

## 2. Functional gaps this restructuring closes

- [x] **`logout()` never called the backend.** `POST /api/users/logout` revokes the JWT
  (adds its `jti` to the server-side blocklist); `UserService.logout()` used to only clear
  `localStorage` and reset the local signals, so a "logged out" token was still valid
  server-side until it naturally expired. Fixed ahead of the rename/merge (done directly in
  `user-service.ts` during a 1:1 backend-endpoint-coverage pass): `logout()` still clears
  local state synchronously (same call site, same void signature - no component changes
  needed), but now also fires the revoke request in the background with the pre-clear
  token attached explicitly, since the auth interceptor reads the live (now-cleared) signal.
- [x] **No `updateUser()`/`deleteUser()` on the frontend at all**, even though the backend
  has had `PATCH`/`DELETE /api/users/<id>` all along. Added directly to `user-service.ts`
  in the same pass - `updateUser()` PATCHes and syncs the result back into `currentUser`/
  `localStorage`; `deleteUser()` DELETEs and clears the session. Not yet wired into any
  component (no profile-edit/delete-account UI calls them yet) - that's a components-layer
  follow-up, not a services-layer gap.
- [ ] **Leftover debug `console.log()`s** in `recipe.service.ts` (logs the API URL; one bare
  call) and `user-service.ts` (logs the API URL and full `fullApiUrl` on every login
  attempt). Removed while those files are being edited for the reasons above.

## Explicitly out of scope for this pass

- `RecipeService.toggleFavorite()` is local-only optimistic state with no backing endpoint
  (there is no favorites endpoint on the backend at all) - a refresh silently reverts it.
  This is a feature gap, not a structural one; worth its own pass once there's a backend
  endpoint to call.
- Restructuring `components/` itself (e.g. `features/`-style grouping) - not requested,
  and the components layer isn't where the duplication/inconsistency actually is today.

---

**Order of attack:** rename → extract models → merge services → relocate interceptor → add
guard → standardize error handling → (functional gaps fall out of the merge naturally).
