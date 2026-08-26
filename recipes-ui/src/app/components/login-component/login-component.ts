import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

// Angular Material Imports
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UserService } from '../../services/user-service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './login-component.html',
  styleUrl: './login-component.css',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(UserService);
  private router = inject(Router);
  private snackBar = inject(MatSnackBar);

  // State Signals
  readonly isLoading = signal(false);
  readonly hidePassword = signal(true);

  // Reactive Form definition
  readonly loginForm = this.fb.nonNullable.group({
    usernameOrEmail: ['sami_cooks', [Validators.required]],
    password: ['SamiSecretPass123!', [Validators.required, Validators.minLength(6)]],
  });

  togglePasswordVisibility(): void {
    this.hidePassword.update((val) => !val);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    const credentials = this.loginForm.getRawValue();

    this.authService.login(credentials).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.snackBar.open(`Welcome back, ${response.user.name}!`, 'Close', {
          duration: 3000,
        });
        this.router.navigate(['/explore']);
      },
      error: (err) => {
        this.isLoading.set(false);
        console.error('Login failed:', err);
        this.snackBar.open(err.error?.message || 'Invalid username or password.', 'Dismiss', {
          duration: 5000,
          panelClass: ['error-snackbar'],
        });
      },
    });
  }
}
