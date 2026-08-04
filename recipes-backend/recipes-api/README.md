# recipes-api

A RESTful backend service built with **Flask**, **SQLAlchemy**, and **PostgreSQL** for managing recipes, ingredients, dynamic recipe parts, and user authentication.

---

## Features

- **User Authentication:** Registration and Login with password hashing and JWT (JSON Web Token) authentication.
- **Recipe Management:** Complete CRUD operations for recipes, nested parts, and ingredients.
- **Authorization Checks:** Ownership-restricted routes for editing and deleting recipes.
- **Database & ORM:** PostgreSQL integration with SQLAlchemy 2.0.
- **Automated Testing:** Unit test suite powered by `unittest` using an isolated in-memory SQLite database.

---

## Tech Stack

- **Framework:** Python 3.10+, Flask
- **Database:** PostgreSQL (Production/Dev), SQLite (Testing)
- **ORM:** SQLAlchemy 2.0 (Flask-SQLAlchemy)
- **Authentication:** Flask-JWT-Extended
- **CORS Support:** Flask-CORS

---

## Project Structure

```text
recipes-backend/recipes-api/
├── controllers/
│   ├── recipe_controller.py   # Business logic for recipes & dynamic parts
│   └── user_controller.py     # Business logic for registration & auth
├── models/
│   ├── recipe.py              # Recipe, RecipePart, and Ingredient models
│   └── user.py                # User model and db instance
├── views/
│   ├── recipe_views.py        # Blueprint endpoints for /api/recipes
│   └── user_views.py          # Blueprint endpoints for /api/users
├── tests/
│   ├── test_base.py           # Base test configuration and SQLite fixtures
│   ├── test_users.py          # Authentication & user management tests
│   └── test_recipes.py        # Recipe CRUD integration tests
├── app.py                     # Application entry point & configuration
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables