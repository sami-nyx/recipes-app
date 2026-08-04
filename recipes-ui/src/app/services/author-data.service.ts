import { Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { delay } from 'rxjs/operators';

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

  getAuthorById(id: string): Observable<AuthorData> {
    const author = this.mockAuthors.find(a => a.id === id || a.username === id);

    if (author) {
      return of({ ...author }).pipe(delay(500));
    }

    return throwError(() => new Error(`Author with ID "${id}" not found.`)).pipe(delay(500));
  }
}