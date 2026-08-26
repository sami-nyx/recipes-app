import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog } from '@angular/material/dialog';
import { AuthorData, AuthorDataService } from '../../services/author-data.service';
import { MatDividerModule } from '@angular/material/divider';
import { UserService } from '../../services/user-service';
import { EditProfileDialogComponent } from '../edit-profile-dialog/edit-profile-dialog';

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
  styleUrl: './user-bio-component.css',
})
export class UserBioComponent {
  private authorService = inject(AuthorDataService);
  private userService = inject(UserService);
  private dialog = inject(MatDialog);

  readonly currentUser = this.userService.currentUser;
  readonly isAuthenticated = this.userService.isAuthenticated;
  readonly isOwner = computed(() => this.userService.isOwner(this.authorId()));

  authorId = input.required<string>();

  // State signals
  userData = signal<AuthorData | null>(null);
  isLoading = signal<boolean>(false);
  hasError = signal<boolean>(false);
  isFollowing = signal<boolean>(false);

  constructor() {
    effect(() => {
      this.loadAuthor(this.authorId());
    });
  }

  private loadAuthor(authorId: string): void {
    if (!authorId) {
      this.isLoading.set(false);
      return;
    }

    this.isLoading.set(true);
    this.hasError.set(false);

    this.authorService.getAuthorById(authorId).subscribe({
      next: (data) => {
        this.userData.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to load author profile:', err);
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  onFollowClick(event: MouseEvent): void {
    event.stopPropagation();
    this.isFollowing.update((state) => !state);
  }

  onEditClick(): void {
    const user = this.currentUser();
    if (!user) {
      return;
    }

    const dialogRef = this.dialog.open(EditProfileDialogComponent, {
      width: '420px',
      data: { user },
    });

    // The dialog itself already updated UserService's currentUser signal -
    // re-fetch here only to refresh this page's separate `userData` (the
    // public AuthorData view of the same profile, sourced from a
    // different endpoint) with the edited name/avatar/bio.
    dialogRef.afterClosed().subscribe((updatedUser) => {
      if (updatedUser) {
        this.loadAuthor(this.authorId());
      }
    });
  }
}
