import { inject, Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

export interface AuthorData {
  id: string;
  name: string;
  username: string;
  avatarUrl?: string;
  bio?: string;
  recipesCount: number;
  followersCount: number;
  joinedDate?: Date | string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthorDataService {

  constructor(private http: HttpClient) {}

  private readonly apiUrl = `${environment.fullApiUrl}/users`;
  

  getAuthorById(id: string): Observable<AuthorData> {
  // Directly return the HTTP request Observable
  return this.http.get<AuthorData>(`${this.apiUrl}/author/${id}`);
}
  }
