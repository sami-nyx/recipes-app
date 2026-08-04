import { Component, effect, inject, input, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthorData, AuthorDataService } from '../../services/author-data.service';
import { MatDividerModule } from '@angular/material/divider';
import { UserService } from '../../services/user-service';

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
  private userDataService = inject(AuthorDataService);
  private userService = inject(UserService);
readonly currentUser = this.userService.currentUser;
  readonly isAuthenticated = this.userService.isAuthenticated;
  // 1. Change input.required to optional input signal
  authorId = input<string>();

  // State signals
  userData = signal<AuthorData | null>(null);
  isLoading = signal<boolean>(false);
  hasError = signal<boolean>(false);
  isFollowing = signal<boolean>(false);

  constructor() {
    effect(() => {
      const id = this.authorId();
      console.log("id:")
      console.log(id)
      // 2. Safely guard against undefined/null initial state
      if (!id) {
        this.isLoading.set(false);
        return;
      }

      this.isLoading.set(true);
      this.hasError.set(false);

      this.userDataService.getAuthorById(id).subscribe({
        next: (data) => {
          this.userData.set(data);
          this.isLoading.set(false);
        },
        error: (err) => {
          console.error(err);
          this.hasError.set(true);
          this.isLoading.set(false);
        }
      });
    });
  }

  onFollowClick(event: MouseEvent): void {
    event.stopPropagation();
    this.isFollowing.update(state => !state);
  }
}