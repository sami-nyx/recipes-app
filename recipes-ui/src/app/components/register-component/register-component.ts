import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

// Material Imports
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RegisterUserDto, UserService } from '../../services/user-service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './register-component.html',
  styleUrl: './register-component.css',
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private router = inject(Router);
  private snackBar = inject(MatSnackBar);

  isLoading = signal(false);
  hidePassword = signal(true);

  // Pre-filled default values for quick testing
  registerForm = this.fb.nonNullable.group({
    name: ['Sami Khoury', [Validators.required, Validators.minLength(2)]],
    username: [
      'sami_cooks',
      [Validators.required, Validators.minLength(3), Validators.pattern(/^[a-zA-Z0-9_]+$/)],
    ],
    email: ['sami@example.com', [Validators.required, Validators.email]],
    password: ['SamiSecretPass123!', [Validators.required, Validators.minLength(8)]],
    avatarUrl: ['https://i.pravatar.cc/150?img=33', [Validators.pattern(/^https?:\/\/.+/)]],
    bio: [
      "Hi, I'm Sami! Passionate home chef who loves grilled dishes and Mediterranean baking.",
      [Validators.maxLength(250)],
    ],
  });

  togglePasswordVisibility(event: MouseEvent) {
    event.preventDefault();
    this.hidePassword.update((v) => !v);
  }

  onSubmit() {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    const userData: RegisterUserDto = this.registerForm.getRawValue();

    this.userService.registerUser(userData).subscribe({
      next: (response) => {
        this.isLoading.set(false);

        // Token & User are already saved by UserService tap operator!
        this.snackBar.open(`Welcome, ${response.user.name}!`, 'Close', { duration: 3000 });
        this.router.navigate(['/explore']);
      },
      error: (err) => {
        this.isLoading.set(false);
        console.error('Registration failed:', err);

        this.snackBar.open(
          err.error?.message || 'Registration failed. Please try again.',
          'Dismiss',
          {
            duration: 5000,
            panelClass: ['error-snackbar'],
          },
        );
      },
    });
  }
}
