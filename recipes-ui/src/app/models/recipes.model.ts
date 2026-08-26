import { Author } from './author.model';

export interface Ingredient {
  id?: string;
  name: string;
  amount: number; // e.g., 200
  unit: string; // e.g., "g", "ml", "tbsp"
  costPer100g?: number; // e.g., 1.50 ($/€ per 100g)
  caloriesPer100g?: number; // e.g., 165 (kcal per 100g)
}

export interface RecipePart {
  id?: string;
  title: string; // e.g., "Marinade", "Dressing", "Assembly"
  instructions: string[]; // Sequential steps for this specific part
  ingredients?: Ingredient[]; // Optional part-specific ingredient list
}

// Mirrors the backend's SORT_OPTIONS whitelist (recipe_controller.py) -
// keep these two lists in sync.
export type RecipeSort = 'newest' | 'prepTime' | 'calories' | 'cost';

export interface Recipe {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  prepTimeMinutes: number;
  cookTimeMinutes: number;
  servings: number;
  totalWeightGrams?: number;
  costPer100g?: number;
  caloriesPer100g?: number;
  parts: RecipePart[];
  favsCount: number;
  createdAt: Date | string;
  isStarred?: boolean; // Added optional property
  author: Author;
}
