import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Recipe } from '../../models/recipes.model';
import { RecipeService } from '../../services/recipe.service';

// Angular Material Imports
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatListModule } from '@angular/material/list';

@Component({
  selector: 'app-view-recipe',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatListModule
  ],
  templateUrl: './view-recipe-component.html',
  styleUrl: './view-recipe-component.css'
})
export class ViewRecipeComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private recipeService = inject(RecipeService);

  // Explicitly allow null or undefined so signals stay type-safe
  recipe = signal<Recipe | null>(null);
  isLoading = signal<boolean>(true);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.fetchRecipe(id);
    } else {
      this.isLoading.set(false);
    }
  }

  fetchRecipe(id: string): void {
    this.recipeService.getRecipeById(id).subscribe({
      next: (data) => {
        // Fallback undefined to null to match Recipe | null
        this.recipe.set(data ?? null);
        this.isLoading.set(false);
      },
      error: () => {
        this.recipe.set(null);
        this.isLoading.set(false);
      }
    });
  }

  toggleFavorite(): void {
    const current = this.recipe();
    if (current) {
      const isStarred = !current.isStarred;
      const favsCount = current.favsCount + (isStarred ? 1 : -1);

      const updatedRecipe: Recipe = {
        ...current,
        isStarred,
        favsCount
      };

      this.recipe.set(updatedRecipe);
      this.recipeService.toggleFavorite(updatedRecipe.id, isStarred);
    }
  }

  goBack(): void {
    this.router.navigate(['/explore'])
  }
}