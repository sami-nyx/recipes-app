# 🍳 Culinary Connect

**Culinary Connect** is a modern, responsive web application built with Angular and Angular Material. It allows food enthusiasts to discover recipes, share culinary experiences, leave ratings and reviews, save favorite dishes, and contribute original recipes to the community.

---

## 🌟 Key Features (Phase 1 MVP)

* **🔐 User Authentication:** Secure sign-in and sign-up interface with protected application routes.
* **🔍 Recipe Discovery:** Explore a catalog of recipes with real-time keyword search filtering.
* **❤️ Favorites Management:** One-click bookmarking to save and manage favorite recipes in a personal collection.
* **⭐ Reviews & Ratings:** Interactive 5-star rating system and text review feedback on recipe pages.
* **➕ Recipe Submission:** Dynamic multi-step creation form to submit recipes complete with ingredients, preparation steps, times, and calorie details.

---

## 🛠️ Built With

* **Frontend Framework:** [Angular](https://angular.dev/) (Standalone Components & Signals)
* **UI Component Library:** [Angular Material](https://material.angular.io/)
* **Icons:** Material Icons
* **Language:** TypeScript
* **Styling:** SCSS / CSS

---

## 📁 Project Structure

```text
src/app/
├── core/                        # Application singletons (Guards, Services, Interceptors)
│   ├── guards/                  # Auth Guards for route protection
│   └── services/                # AuthService, RecipeService (Signal-based state)
├── features/                    # Feature views
│   ├── auth/                    # Sign-in and Sign-up components
│   ├── recipe-catalog/          # Main feed grid & Keyword Search
│   ├── recipe-detail/           # Detail view, reviews list, and review form
│   ├── recipe-form/             # Recipe submission form with dynamic lists
│   └── favorites/               # Saved user favorites grid
├── shared/                      # Reusable components, directives, & models
│   ├── components/              # Shared UI cards, star rating displays
│   └── models/                  # TypeScript interfaces (Recipe, Review, User)
└── app.routes.ts                # Application routes with lazy-loaded features