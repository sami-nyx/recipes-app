import { Component, inject } from '@angular/core';
import { signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { UpdateUserDto, User, UserService } from '../../services/user-service';

export interface EditProfileDialogData {
  user: User;
}

/**
 * Edit-profile form, shared by every place a user can edit their own
 * profile (the personal/account panel, and their own public bio page) -
 * one dialog, one PATCH /api/users/<id> call site, instead of duplicating
 * the form per caller.
 */
@Component({
  selector: 'app-edit-profile-dialog',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './edit-profile-dialog.html',
  styleUrl: './edit-profile-dialog.css',
})
export class EditProfileDialogComponent {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  readonly dialogRef = inject(MatDialogRef<EditProfileDialogComponent>);
  readonly data = inject<EditProfileDialogData>(MAT_DIALOG_DATA);

  isSaving = signal(false);
  errorMessage = signal<string | null>(null);

  form = this.fb.nonNullable.group({
    name: [this.data.user.name, [Validators.required, Validators.minLength(2)]],
    avatarUrl: [this.data.user.avatarUrl ?? '', [Validators.pattern(/^https?:\/\/.+/)]],
    bio: [this.data.user.bio ?? '', [Validators.maxLength(250)]],
  });

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    // Empty strings mean "cleared by the user" - send null so the backend
    // stores it as unset rather than an empty string.
    const payload: UpdateUserDto = {
      name: raw.name,
      avatarUrl: raw.avatarUrl.trim() || null,
      bio: raw.bio.trim() || null,
    };

    this.isSaving.set(true);
    this.errorMessage.set(null);

    this.userService.updateUser(this.data.user.id, payload).subscribe({
      next: (response) => {
        this.isSaving.set(false);
        this.dialogRef.close(response.user);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.errorMessage.set(err.error?.message || 'Failed to update profile. Please try again.');
      },
    });
  }
}
