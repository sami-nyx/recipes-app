import { CommonModule } from '@angular/common';
import { Component, input, output, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router'; // 1. Import Router & RouterLink
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Recipe } from '../../models/recipes.model';
import { UserService } from '../../services/user-service';
import { ConfirmDialogComponent } from './confirm-dialog-component/confirm-dialog-component';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-recipe-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule],
  templateUrl: './recipe-card.html',
  styleUrl: './recipe-card.css',
})
export class RecipeCard {
  // private router = inject(Router); // Optional: if you need programmatic navigation

  recipe = input.required<Recipe>();
  deleteClick = output<Recipe>(); // <--- New delete output
  // Outputs for user actions

  favoriteToggle = output<Recipe>();
  cardClick = output<Recipe>(); // recipe id
  authorClick = output<Recipe>(); // author id or username

  private router = inject(Router);
  private userService = inject(UserService);
  private dialog = inject(MatDialog); // <--- Inject MatDialog
  readonly isAuthenticated = this.userService.isAuthenticated;

  isOwner(): boolean {
    return this.userService.isOwner(this.recipe().author?.id);
  }
  onEdit(event: Event): void {
    event.stopPropagation(); // Stop card click from triggering
    // Adjust route path to match your App Routing setup
    this.router.navigate(['/recipes', this.recipe().id, 'edit']);
  }
  onCardClick(event?: MouseEvent): void {
    if (event) {
      event.stopPropagation(); // Prevents bubbling up to outer elements
    }
    this.cardClick.emit(this.recipe());
  }

  onAuthorClick(event: MouseEvent): void {
    event.stopPropagation(); // Prevents triggering onCardClick
    this.authorClick.emit(this.recipe()); // or recipe().author.id
  }

  onToggleFavorite(event: Event): void {
    event.stopPropagation();
    const currentRecipe = this.recipe();
    // Local-only: there's no favorites endpoint on the backend, so this
    // just flips isStarred/favsCount in memory via RecipeService - it
    // isn't persisted and will revert on refresh.
    currentRecipe.isStarred = !currentRecipe.isStarred;
    this.favoriteToggle.emit(currentRecipe);
  }
  onDelete(event: Event): void {
    event.stopPropagation(); // Stop card click navigation

    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '380px',
      data: {
        title: 'Delete Recipe',
        message: `Are you sure you want to delete "${this.recipe().title}"? This action cannot be undone.`,
        confirmText: 'Delete',
        cancelText: 'Cancel',
      },
    });

    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.deleteClick.emit(this.recipe());
      }
    });
  }
}
