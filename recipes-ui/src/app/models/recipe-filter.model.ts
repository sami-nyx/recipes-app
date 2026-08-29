export interface RecipeFilter {
  query: string;
  maxPrepTime: number;
  onlyMyRecipes?: boolean;
  // Matched against the recipe author's username or display name
  // (case-insensitive substring) - independent of onlyMyRecipes, so you
  // can browse one other contributor's recipes without it being you.
  contributor?: string;
}
