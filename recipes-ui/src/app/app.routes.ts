import { Routes } from '@angular/router';
import { Landing } from './components/landing/landing';
import { ExploreComponent } from './components/explore/explore';
import { ViewRecipeComponent } from './components/view-recipe-component/view-recipe-component';
import { UserBioComponent } from './components/user-bio-component/user-bio-component';
import { RegisterComponent } from './components/register-component/register-component';
import { LoginComponent } from './components/login-component/login-component';
import { RecipeFormComponent } from './components/recipe-form-component/recipe-form-component';

export const routes: Routes = [
  { path: '', component: Landing },
  { path: 'explore', component: ExploreComponent },
  { path: 'recipes/:id/edit', component: RecipeFormComponent },
  { path: 'recipes/create', component: RecipeFormComponent },
  { path: 'recipes/:id', component: ViewRecipeComponent },
  { path: 'user/:authorId', component: UserBioComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: '**', redirectTo: '' }
];