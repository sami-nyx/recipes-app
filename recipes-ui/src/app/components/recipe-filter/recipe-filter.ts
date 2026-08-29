import { Component, inject, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatSliderModule } from '@angular/material/slider';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle'; // <--- Import MatSlideToggle
import { RecipeFilter } from '../../models/recipe-filter.model';
import { UserService } from '../../services/user-service';

@Component({
  selector: 'app-recipe-filter',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatSliderModule,
    MatButtonModule,
    MatSlideToggleModule, // <--- Add to imports
  ],
  templateUrl: './recipe-filter.html',
  styleUrl: './recipe-filter.css',
})
export class RecipeFilterComponent {
  filterChange = output<RecipeFilter>();

  private userService = inject(UserService);
  readonly isAuthenticated = this.userService.isAuthenticated;

  searchQuery = signal<string>('');
  maxPrepTime = signal<number>(60);
  onlyMyRecipes = signal<boolean>(false); // <--- New Signal
  contributor = signal<string>('');

  onFilterUpdated(): void {
    this.filterChange.emit({
      query: this.searchQuery(),
      maxPrepTime: this.maxPrepTime(),
      onlyMyRecipes: this.onlyMyRecipes(),
      contributor: this.contributor(),
    });
  }

  resetFilters(): void {
    this.searchQuery.set('');
    this.maxPrepTime.set(60);
    this.onlyMyRecipes.set(false);
    this.contributor.set('');
    this.onFilterUpdated();
  }
}
