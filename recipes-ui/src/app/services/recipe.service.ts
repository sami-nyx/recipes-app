import { Injectable, signal, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, tap, catchError } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { Recipe } from '../models/recipes.model';
import { Author } from '../models/author.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class RecipeService {
  private http = inject(HttpClient);
  private readonly apiUrl = `${environment.fullApiUrl}/recipes`;

  private recipesSignal = signal<Recipe[]>([]);

// Read-only signal exposed to components
public readonly recipes = this.recipesSignal.asReadonly();

/**
 * Fetches recipes from backend API and updates the reactive signal
 */
getRecipes(): Observable<Recipe[]> {
  console.log(this.apiUrl)
  return this.http.get<Recipe[]>(this.apiUrl).pipe(
    tap((dbRecipes: Recipe[]) => {
      // Update the signal with ONLY backend recipes
      this.recipesSignal.set(dbRecipes);
    }),
    catchError((error) => {
      console.error('Failed to load recipes from backend:', error);
      // Fallback to empty array so components don't crash
      this.recipesSignal.set([]);
      return of([]); // Requires importing 'of' from 'rxjs'
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
    console.log()
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

