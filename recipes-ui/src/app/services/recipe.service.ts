import { Injectable, signal, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, tap, catchError } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { Recipe } from '../models/recipes.model';
import { Author } from '../models/author.model';

@Injectable({
  providedIn: 'root'
})
export class RecipeService {
  private http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:5000/api/recipes';

  // Signal holding the master list of recipes initialized with mock data
  private recipesSignal = signal<Recipe[]>(MOCK_RECIPES);

  // Read-only signal exposed to components
  public readonly recipes = this.recipesSignal.asReadonly();

  /**
   * Fetches recipes from backend API and combines them with MOCK_RECIPES
   */
  getRecipes(): Observable<Recipe[]> {
    return this.http.get<Recipe[]>(this.apiUrl).pipe(
      map((backendRecipes: Recipe[]) => {
        // Merge real DB recipes with static MOCK_RECIPES
        console.log(backendRecipes)
        return [...backendRecipes, ...MOCK_RECIPES];
      }),
      tap((combinedRecipes: Recipe[]) => {
        // Update the signal so all components bound to recipeService.recipes reactively update
        this.recipesSignal.set(combinedRecipes);
      }),
      catchError((error) => {
        console.warn('Backend API unavailable. Falling back to mock recipes.', error);
        this.recipesSignal.set(MOCK_RECIPES);
        return of(MOCK_RECIPES);
      })
    );
  }

  /**
 * Delete a recipe by ID
 */
deleteRecipe(id: string): Observable<void> {
  return this.http.delete<void>(`${this.apiUrl}/${id}`).pipe(
    tap(() => {
      // Remove the deleted recipe from local state
      this.recipesSignal.update(recipes => recipes.filter(r => r.id !== id));
    }),
    catchError(error => {
      console.error(`Failed to delete recipe with ID ${id}:`, error);
      throw error;
    })
  );
}

  /**
   * Fetches a single recipe by ID (checks signal cache first, then fallback)
   */
  getRecipeById(id: string): Observable<Recipe | undefined> {
    const cachedRecipe = this.recipesSignal().find(r => r.id === id);
    if (cachedRecipe) {
      return of(cachedRecipe);
    }
    return this.http.get<Recipe>(`${this.apiUrl}/${id}`).pipe(
      catchError(() => of(undefined))
    );
  }

  /**
   * Create a new recipe and append it to local signal cache
   */
  createRecipe(recipe: Partial<Recipe>): Observable<Recipe> {
    return this.http.post<Recipe>(`${this.apiUrl}/create`, recipe).pipe(
      tap((newRecipe: Recipe) => {
        this.recipesSignal.update(current => [newRecipe, ...current]);
      })
    );
  }

  /**
   * Update an existing recipe by ID
   */
  updateRecipe(id: string, recipe: Partial<Recipe>): Observable<Recipe> {
    return this.http.put<Recipe>(`${this.apiUrl}/${id}`, recipe).pipe(
      tap((updated: Recipe) => {
        this.recipesSignal.update(recipes =>
          recipes.map(r => (r.id === id ? { ...r, ...updated } : r))
        );
      })
    );
  }

  /**
   * Toggles the favorite status and updates favsCount in memory
   */
  toggleFavorite(recipeId: string, isFav: boolean): void {
    this.recipesSignal.update(recipes =>
      recipes.map(recipe => {
        if (recipe.id === recipeId) {
          const newFavCount = isFav ? recipe.favsCount + 1 : Math.max(0, recipe.favsCount - 1);
          return { ...recipe, favsCount: newFavCount };
        }
        return recipe;
      })
    );
  }
}

export const MOCK_AUTHORS: Record<string, Author> = {
  alex: {
    id: 'usr-1',
    name: 'Alex Chen',
    username: 'chef_alex',
    avatarUrl: 'https://i.pravatar.cc/150?img=11',
    bio: 'Home cook passionate about high-protein recipes and meal prep.',
    recipesCount: 14
  },
  maya: {
    id: 'usr-2',
    name: 'Maya Lin',
    username: 'maya_bakes',
    avatarUrl: 'https://i.pravatar.cc/150?img=32',
    bio: 'Pastry chef and sourdough enthusiast.',
    recipesCount: 29
  }
};
// ==========================================
// MOCK DATA
// ==========================================
const MOCK_RECIPES: Recipe[] = [
  {
    id: 'rec-1',

    author: MOCK_AUTHORS['maya'],
    title: 'Smokey Smash Burgers',
    description: 'Crispy-edged beef patties with melted cheddar, caramelized onions, and secret sauce on toasted brioche.',
    imageUrl: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600',
    prepTimeMinutes: 15,
    cookTimeMinutes: 10,
    servings: 4,
    totalWeightGrams: 650,
    costPer100g: 1.85,
    caloriesPer100g: 260,
    favsCount: 42,
    createdAt: '2026-07-15T10:30:00Z',
    parts: [
      {
        id: 'p-1',
        title: 'Secret Sauce',
        instructions: [
          'Whisk mayonnaise, yellow mustard, sweet pickle relish, and smoked paprika in a small bowl.',
          'Chill in the refrigerator for at least 15 minutes before serving.'
        ],
        ingredients: [
          { name: 'Mayonnaise', amount: 100, unit: 'g', costPer100g: 0.80, caloriesPer100g: 680 },
          { name: 'Yellow Mustard', amount: 20, unit: 'g', costPer100g: 0.60, caloriesPer100g: 60 },
          { name: 'Sweet Pickle Relish', amount: 30, unit: 'g', costPer100g: 0.90, caloriesPer100g: 120 }
        ]
      },
      {
        id: 'p-2',
        title: 'Beef Patties & Assembly',
        instructions: [
          'Divide ground beef into 4 equal balls without overworking the meat.',
          'Heat a cast-iron skillet over high heat until smoking.',
          'Place beef ball onto skillet and smash flat with a heavy spatula.',
          'Season with salt and pepper. Sear for 2 minutes until edges are crispy, flip, and add cheese.'
        ],
        ingredients: [
          { name: '80/20 Ground Beef', amount: 450, unit: 'g', costPer100g: 2.10, caloriesPer100g: 254 },
          { name: 'Cheddar Cheese Slices', amount: 4, unit: 'slices', costPer100g: 1.50, caloriesPer100g: 400 },
          { name: 'Brioche Buns', amount: 4, unit: 'buns', costPer100g: 1.20, caloriesPer100g: 280 }
        ]
      }
    ]
  },
  {
    id: 'rec-2',
    title: 'Creamy Tuscan Garlic Chicken',
    author: MOCK_AUTHORS['alex'],
    description: 'Pan-seared chicken breasts in a rich garlic cream sauce with sun-dried tomatoes and fresh spinach.',
    imageUrl: 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=600',
    prepTimeMinutes: 10,
    cookTimeMinutes: 20,
    servings: 3,
    totalWeightGrams: 750,
    costPer100g: 2.10,
    caloriesPer100g: 195,
    favsCount: 89,
    createdAt: '2026-07-28T14:15:00Z',
    parts: [
      {
        id: 'p-3',
        title: 'Chicken & Sauce Base',
        instructions: [
          'Season chicken breasts with Italian seasoning, salt, and black pepper.',
          'Sear in olive oil for 5 minutes per side until golden brown. Remove and set aside.',
          'In the same skillet, sauté minced garlic and chopped sun-dried tomatoes for 1 minute.',
          'Pour in heavy cream and chicken broth; bring to a simmer.',
          'Stir in fresh spinach and parmesan cheese until spinach is wilted. Return chicken to pan.'
        ],
        ingredients: [
          { name: 'Chicken Breast', amount: 400, unit: 'g', costPer100g: 1.90, caloriesPer100g: 165 },
          { name: 'Heavy Cream', amount: 200, unit: 'ml', costPer100g: 1.10, caloriesPer100g: 340 },
          { name: 'Sun-dried Tomatoes', amount: 50, unit: 'g', costPer100g: 3.20, caloriesPer100g: 213 },
          { name: 'Fresh Spinach', amount: 100, unit: 'g', costPer100g: 1.40, caloriesPer100g: 23 }
        ]
      }
    ]
  },
  {
    id: 'rec-3',
    author: MOCK_AUTHORS['alex'],
    title: 'Crispy Tofu Buddha Bowl',
    description: 'Sesame-glazed crispy baked tofu served over quinoa, steamed edamame, shredded red cabbage, and peanut dressing.',
    imageUrl: '', // Testing optional image fallback
    prepTimeMinutes: 20,
    cookTimeMinutes: 25,
    servings: 2,
    totalWeightGrams: 550,
    costPer100g: 1.15,
    caloriesPer100g: 145,
    favsCount: 27,
    createdAt: '2026-08-01T09:00:00Z',
    parts: [
      {
        id: 'p-4',
        title: 'Crispy Tofu',
        instructions: [
          'Press tofu to remove excess moisture and cut into 1/2-inch cubes.',
          'Toss cubes with soy sauce, sesame oil, and cornstarch until evenly coated.',
          'Bake at 200°C (400°F) for 25 minutes, flipping halfway through.'
        ],
        ingredients: [
          { name: 'Extra Firm Tofu', amount: 300, unit: 'g', costPer100g: 0.90, caloriesPer100g: 144 },
          { name: 'Cornstarch', amount: 15, unit: 'g', costPer100g: 0.30, caloriesPer100g: 381 }
        ]
      },
      {
        id: 'p-5',
        title: 'Peanut Lime Dressing',
        instructions: [
          'Whisk peanut butter, lime juice, soy sauce, maple syrup, and warm water until smooth.'
        ],
        ingredients: [
          { name: 'Peanut Butter', amount: 40, unit: 'g', costPer100g: 1.20, caloriesPer100g: 588 },
          { name: 'Lime Juice', amount: 20, unit: 'ml', costPer100g: 0.80, caloriesPer100g: 25 }
        ]
      }
    ]
  }
];