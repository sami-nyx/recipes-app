import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment.development';
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
@Injectable({
  providedIn: 'root'
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
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, userData).pipe(
      tap((response) => this.handleAuthentication(response))
    );
  }


  login(credentials: any): Observable<AuthResponse> {

  console.log(environment.fullApiUrl)
  console.log("apiURL:", this.apiUrl)
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap((response) => this.handleAuthentication(response))
    );
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.token.set(null);
    this.currentUser.set(null);
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