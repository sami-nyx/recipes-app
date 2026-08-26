import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import { environment } from '../../environments/environment';
export interface RegisterUserDto {
  name: string;
  username: string;
  email: string;
  password?: string;
  bio?: string;
  avatarUrl?: string;
}

export interface User {
  id: string;
  name: string;
  username: string;
  email: string;
  avatarUrl?: string;
  bio?: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
}

export interface UpdateUserDto {
  name?: string;
  avatarUrl?: string | null;
  bio?: string | null;
}

export interface UpdateUserResponse {
  message: string;
  user: User;
}
@Injectable({
  providedIn: 'root',
})
export class UserService {
  private readonly apiUrl = `${environment.fullApiUrl}/users`;
  private readonly TOKEN_KEY = 'recipes_jwt_token';
  private readonly USER_KEY = 'recipes_user_data';

  // Using Angular Signals for reactive state (Angular 16+)
  currentUser = signal<User | null>(this.getStoredUser());
  token = signal<string | null>(this.getStoredToken());
  isAuthenticated = computed(() => !!this.token());

  constructor(private http: HttpClient) {}
  registerUser(userData: any): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.apiUrl}/register`, userData)
      .pipe(tap((response) => this.handleAuthentication(response)));
  }

  login(credentials: any): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.apiUrl}/login`, credentials)
      .pipe(tap((response) => this.handleAuthentication(response)));
  }

  /**
   * Logs out locally (instant - the caller doesn't need to subscribe to
   * anything) and best-effort revokes the JWT server-side so it can't be
   * replayed after logout, via POST /api/users/logout.
   *
   * The revoke request is sent with the *current* token attached
   * explicitly, before local state is cleared - the auth interceptor
   * reads the token from this service's live signal, so firing the
   * request after clearing it would send an unauthenticated request the
   * backend can't identify a token to revoke from.
   */
  logout(): void {
    const token = this.token();

    this.clearSession();

    if (token) {
      this.http
        .post(
          `${this.apiUrl}/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        )
        .pipe(
          catchError((error) => {
            // Best-effort: local state is already cleared either way, so a
            // failure here just means the token stays valid server-side
            // until it naturally expires - no worse than before this
            // method called the backend at all.
            console.error('Failed to revoke session server-side:', error);
            return of(null);
          }),
        )
        .subscribe();
    }
  }

  /**
   * Updates the current user's editable profile fields (name/avatarUrl/bio)
   * via PATCH /api/users/<id>, and keeps local session state in sync with
   * the result.
   */
  updateUser(userId: string, data: UpdateUserDto): Observable<UpdateUserResponse> {
    return this.http.patch<UpdateUserResponse>(`${this.apiUrl}/${userId}`, data).pipe(
      tap((response) => {
        localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
        this.currentUser.set(response.user);
      }),
    );
  }

  /**
   * Deletes the current user's account via DELETE /api/users/<id>, then
   * clears local session state - there's nothing left to be logged in as.
   */
  deleteUser(userId: string): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`${this.apiUrl}/${userId}`)
      .pipe(tap(() => this.clearSession()));
  }

  /**
   * Checks if the currently logged-in user matches the provided author/user ID
   */
  isOwner(authorId?: string | null): boolean {
    if (!authorId) return false;
    const user = this.currentUser();
    return !!user && user.id === authorId;
  }
  getToken(): string | null {
    return this.token();
  }

  private clearSession(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.token.set(null);
    this.currentUser.set(null);
  }

  private handleAuthentication(response: AuthResponse): void {
    const { accessToken, user } = response;

    // 1. Save to localStorage for persistence
    localStorage.setItem(this.TOKEN_KEY, accessToken);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));

    // 2. Update reactive state
    this.token.set(accessToken);
    this.currentUser.set(user);
  }

  private getStoredToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  private getStoredUser(): User | null {
    const userJson = localStorage.getItem(this.USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  }
}
