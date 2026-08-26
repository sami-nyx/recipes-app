import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { UserService } from '../../../services/user-service';
import { EditProfileDialogComponent } from '../../edit-profile-dialog/edit-profile-dialog';
import { ConfirmDialogComponent } from '../../recipe-card/confirm-dialog-component/confirm-dialog-component';

@Component({
  selector: 'app-authenticated',
  standalone: true,
  imports: [RouterLink, MatCardModule, MatButtonModule, MatIconModule, MatDividerModule],
  templateUrl: './authenticated.html',
  styleUrl: './authenticated.css',
})
export class Authenticated {
  private userService = inject(UserService);
  private router = inject(Router);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  readonly user = this.userService.currentUser;

  logout(): void {
    this.userService.logout();
    this.router.navigate(['/explore']);
  }

  editProfile(): void {
    const user = this.user();
    if (!user) {
      return;
    }

    this.dialog.open(EditProfileDialogComponent, {
      width: '420px',
      data: { user },
    });
  }

  deleteAccount(): void {
    const user = this.user();
    if (!user) {
      return;
    }

    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '380px',
      data: {
        title: 'Delete Account',
        message: 'Are you sure you want to permanently delete your account? This cannot be undone.',
        confirmText: 'Delete Account',
        cancelText: 'Cancel',
      },
    });

    dialogRef.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) {
        return;
      }

      this.userService.deleteUser(user.id).subscribe({
        next: () => {
          this.snackBar.open('Your account has been deleted.', 'Close', { duration: 3000 });
          this.router.navigate(['/']);
        },
        error: (err) => {
          this.snackBar.open(
            err.error?.message || 'Failed to delete account. Please try again.',
            'Dismiss',
            { duration: 5000, panelClass: ['error-snackbar'] },
          );
        },
      });
    });
  }
}
