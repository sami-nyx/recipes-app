import { Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { UserService } from './services/user-service';
@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('recipes-ui');
  private userService = inject(UserService);
  private router = inject(Router);

  // Expose signals from UserService
  readonly isAuthenticated = this.userService.isAuthenticated;
  readonly currentUser = this.userService.currentUser;

  logout(): void {
    this.userService.logout();
    this.router.navigate(['/']);
  }
}
