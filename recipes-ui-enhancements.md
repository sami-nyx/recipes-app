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
- [x] **Leftover debug `console.log()`s** in `recipe.service.ts` (logged the API URL; one
  bare call), `user-service.ts` (logged the API URL and full `fullApiUrl` on every login
  attempt), `user-bio-component.ts` (logged the author id and fetched data on every load),
  and a dead `PersonalComponent.onRegister()` method (unused - `NotAuthenticated`'s CTA
  routes straight to `/login` via `routerLink`, never calls it) with its own stray log.
  Removed in the same pass as wiring the two new methods into the UI (below).

## 3. Wiring `updateUser()`/`deleteUser()`/`getRecipeById()`/`getAuthorById()` into the UI

`getRecipeById()` (`view-recipe-component.ts`) and `getAuthorById()` (`user-bio-component.ts`)
were already wired - verified working, no changes needed beyond the console.log cleanup above.
`updateUser()`/`deleteUser()` had no caller anywhere; closed both gaps:

- [x] **New `EditProfileDialogComponent`** (`components/edit-profile-dialog/`) - a Material
  dialog with a reactive form (name/avatarUrl/bio, same validators as the register form),
  calling `UserService.updateUser()`. One shared component rather than duplicating the form
  per caller, since two different pages need to edit the same profile.
- [x] **Wired into `authenticated.html`** (the signed-in user's own profile panel) - new
  "Edit Profile" button opens the dialog; new "Delete Account" button reuses the existing
  `ConfirmDialogComponent` (already used for recipe deletion) for a confirmation step, then
  calls `UserService.deleteUser()` and navigates home on success.
- [x] **Fixed a broken "Edit Profile" link in `user-bio-component.html`** (the public
  `/user/:authorId` page, shown when viewing your own profile too) - found while wiring this
  up: the markup was malformed (unclosed `<p>`/`<a>` tags) and the link had no click handler
  at all, so it rendered as inert text; `onEditClick()` in the `.ts` file separately navigated
  to `/profile/edit`, a route that doesn't exist in `app.routes.ts` and would have silently
  redirected to the landing page via the wildcard route. Fixed the markup and pointed it at
  the same `EditProfileDialogComponent`; after a successful edit, this page's own `userData`
  (fetched separately, from `GET /api/users/author/<id>`, not the same object as
  `UserService.currentUser`) is explicitly re-fetched so the displayed name/avatar/bio update
  too.
- [x] **Removed two dead stub files**: `confirm-dialog-component.html`/`.css` - the component
  uses an inline `template:` string, so these were never rendered (default Angular CLI
  schematic output, left behind unedited).
- [x] **Ran Prettier (`--write`) across all of `src/`** per the project's existing
  `.prettierrc` - 58 files reformatted, no content changes (verified via `tsc --noEmit` and
  `ng build` both passing before and after).
- [x] `components/register-component/html.back.html` - the unreferenced backup file flagged
  above. Confirmed dead and deleted on request.

Verified: `npx tsc --noEmit` clean and `ng build` succeeds (this project's Karma/Vitest test
runner needs a browser package - `@vitest/browser-playwright` - not installed in this
environment, so the component test suite itself couldn't be executed here).

## 4. Small fixes and polish

- [x] **`explore.html`'s "Sort by" bar wired up to a real `?sort=` param** on the backend
  (see `recipes-api-enhancements.md` item 1) - `RecipeService.getRecipes()` now takes an
  optional `RecipeSort`, `explore.ts` tracks `activeSort` and refetches on change, and the
  four `<span>`s (already fully styled with hover/active states, just never bound to
  anything) now call `onSortChanged()`. Sorting is server-side, matching how pagination
  already works, since re-sorting only the loaded page would be wrong past page 1.
- [x] **Documented `RecipeCard`'s favorite star as local-only** - a comment in both the
  template and `onToggleFavorite()` now says explicitly that there's no favorites endpoint
  on the backend, so toggling it doesn't persist and reverts on refresh (the underlying gap
  itself is still tracked below, unchanged).
- [x] **`.toggle-group` (the "Only My Recipes" toggle's wrapper) had no CSS rule at all** in
  `recipe-filter.css` - along with `.sidebar`/`.filter-group`, also used in the template
  but absent from the stylesheet, suggesting the CSS predates the current template
  structure. Added `margin-bottom: 1.25rem` (matching the file's existing spacing scale) to
  `.toggle-group` specifically; `.sidebar`/`.filter-group` are unaddressed - flagged, not
  fixed, since that's a larger mismatch than what was asked.

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
