import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthorData, AuthorDataService } from '../../services/author-data.service';
import { MatDividerModule } from '@angular/material/divider';
import { UserService } from '../../services/user-service';
import { Recipe } from '../../models/recipes.model';
import { Router } from '@angular/router';

@Component({
  selector: 'app-author-bio',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    
  ],
  templateUrl: './user-bio-component.html',
  styleUrl: './user-bio-component.css'
})
export class UserBioComponent {
  private authorService = inject(AuthorDataService);
  private userService = inject(UserService);
readonly currentUser = this.userService.currentUser;
  readonly isAuthenticated = this.userService.isAuthenticated;
 private router = inject(Router);
  readonly isOwner = computed(() => this.userService.isOwner(this.authorId()));
  
  // 1. Change input.required to optional input signal
  // inputRecipe = input<Recipe>();
  authorId = input.required<string>();
  // State signals
  userData = signal<AuthorData | null>(null);
  isLoading = signal<boolean>(false);
  hasError = signal<boolean>(false);
  isFollowing = signal<boolean>(false);

  constructor() {
    
    effect(() => {
      // const recipe = this.inputRecipe();
      const _authorId=this.authorId()
          console.log(_authorId)
      if (!_authorId) {
        this.isLoading.set(false);
        return;
      }
      
      this.isLoading.set(true);
      this.hasError.set(false);
      
      this.authorService.getAuthorById(_authorId).subscribe({
        next: (data) => {
          console.log(data)
          this.userData.set(data);
          this.isLoading.set(false);
        },
        error: (err) => {
          let data =this.authorService.getMockAuthorById(_authorId)
          if(data  ){

          this.userData.set(data);
          this.isLoading.set(false);

          }else{
          console.error(err);
          this.hasError.set(true);
          this.isLoading.set(false);
          }
        }
      });
    });
  }

  onFollowClick(event: MouseEvent): void {
    event.stopPropagation();
    this.isFollowing.update(state => !state);
  }
  onEditClick(): void {
    this.router.navigate(['/profile/edit']); // Adjust route path as needed
  }
}