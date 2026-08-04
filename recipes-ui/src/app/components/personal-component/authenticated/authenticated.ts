import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { UserService } from '../../../services/user-service';

@Component({
  selector: 'app-authenticated',
  standalone: true,
  imports: [
    RouterLink,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule
  ],
  templateUrl: './authenticated.html',
  styleUrl: './authenticated.css',
})
export class Authenticated {
  private userService = inject(UserService);
  private router = inject(Router);

  readonly user = this.userService.currentUser;

  logout(): void {
    this.userService.logout();
    this.router.navigate(['/explore']);
  }
}