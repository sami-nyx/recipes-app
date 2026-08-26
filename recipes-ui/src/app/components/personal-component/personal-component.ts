import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

// Angular Material Imports
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { NotAuthenticated } from './not-authenticated/not-authenticated';
import { UserService } from '../../services/user-service';
import { Authenticated } from './authenticated/authenticated';
@Component({
  selector: 'app-personal',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    NotAuthenticated,
    Authenticated,
  ],
  templateUrl: './personal-component.html',
  styleUrl: './personal-component.css',
})
export class PersonalComponent {
  private userService = inject(UserService);

  // Expose signals from UserService
  readonly isAuthenticated = this.userService.isAuthenticated;
}
