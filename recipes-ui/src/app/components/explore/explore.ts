import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { RecipeService } from '../../services/recipe.service';
import { UserService } from '../../services/user-service'; // <--- Import UserService
import { RecipeFilter } from '../../models/recipe-filter.model';
import { Recipe } from '../../models/recipes.model';

import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RecipeFilterComponent } from '../recipe-filter/recipe-filter';
import { RecipeCard } from '../recipe-card/recipe-card';
import { MatDividerModule } from '@angular/material/divider';
import { PersonalComponent } from '../personal-component/personal-component';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-explore',
  standalone: true,
  imports: [
    CommonModule,
    RecipeFilterComponent,
    RecipeCard,
    MatIconModule,
    MatProgressSpinnerModule,
    PersonalComponent,
    MatDividerModule,
  ],
  templateUrl: './explore.html',
  styleUrl: './explore.css'
})
export class Explore implements OnInit {
  private router = inject(Router);
  private recipeService = inject(RecipeService);
  private userService = inject(UserService); // <--- Inject UserService

  private snackBar = inject(MatSnackBar);
  isLoading = signal<boolean>(true);
  activeFilter = signal<RecipeFilter>({ query: '', maxPrepTime: 60, onlyMyRecipes: false });
  recipes = this.recipeService.recipes;

  filteredRecipes = computed(() => {
    const filter = this.activeFilter();
    const query = filter.query.toLowerCase().trim();
    const maxTime = filter.maxPrepTime;
    const onlyMine = filter.onlyMyRecipes;
    const currentUserId = this.userService.currentUser()?.id; // Assumes currentUser signal on UserService

    return this.recipes().filter(recipe => {
      const matchesSearch = recipe.title.toLowerCase().includes(query) ||
                            recipe.description.toLowerCase().includes(query);
      const matchesTime = recipe.prepTimeMinutes <= maxTime;
      const matchesAuthor = !onlyMine || (currentUserId && recipe.author?.id === currentUserId);

      return matchesSearch && matchesTime && matchesAuthor;
    });
  });

  ngOnInit(): void {
    this.recipeService.getRecipes().subscribe({
      next: () => this.isLoading.set(false),
      error: () => this.isLoading.set(false)
    });
  }

  onFilterChanged(newFilter: RecipeFilter): void {
    this.activeFilter.set(newFilter);
  }

  toggleFavorite(recipe: Recipe): void {
    recipe.isStarred = !recipe.isStarred;
    this.recipeService.toggleFavorite(recipe.id, recipe.isStarred);
  }

  viewRecipe(recipe: Recipe): void {
     this.router.navigate(['/recipes', recipe.id]);
  }
  
  viewAuthor(recipe: Recipe): void {
     this.router.navigate(['/user', recipe.author.id]);
  }

  deleteRecipe(recipe: Recipe): void {
    
  this.recipeService.deleteRecipe(recipe.id).subscribe({
    next: () => {
      this.snackBar.open(`successfully deleted recipe: ${recipe.title}!`, 'Close', {
          duration: 3000
        });
    },
    error: (err) => console.error('Failed to delete recipe:', err)
  });
}
}