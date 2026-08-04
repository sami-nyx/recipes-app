import { inject, Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment.development';

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
  private mockAuthors: AuthorData[] = [
    {
      id: 'usr-1',
      name: 'Sarah Jenkins',
      username: 'chef_sarah',
      avatarUrl: 'https://i.pravatar.cc/150?img=47',
      bio: 'Passionate home cook, pastry lover, and healthy recipe creator.',
      recipesCount: 24,
      followersCount: 1420,
      joinedDate: '2023-04-15'
    },
    {
      id: 'usr-2',
      name: 'Marco Rossi',
      username: 'italian_kitchen',
      avatarUrl: 'https://i.pravatar.cc/150?img=12',
      bio: 'Traditional Italian recipes straight from Nonna’s cookbook.',
      recipesCount: 38,
      followersCount: 3890,
      joinedDate: '2022-09-01'
    }
  ];

  getMockAuthorById(id: string){
    const authorData =this.mockAuthors.find(author => author.id === id);
    

    if (authorData) {
      return authorData;
    }

    return null;
  }

  getAuthorById(id: string): Observable<AuthorData> {
  // Directly return the HTTP request Observable
  return this.http.get<AuthorData>(`${this.apiUrl}/author/${id}`);
}
  }
