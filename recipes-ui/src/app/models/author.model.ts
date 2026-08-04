export interface Author {
  id: string;
  name: string;
  username: string;
  avatarUrl?: string;     // URL to profile avatar image
  bio?: string;
  recipesCount?: number;  // Total recipes published
}