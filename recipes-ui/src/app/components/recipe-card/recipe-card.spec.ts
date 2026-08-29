import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { RecipeCard } from './recipe-card';
import { Recipe } from '../../models/recipes.model';

const mockRecipe: Recipe = {
  id: 'recipe-1',
  title: 'Tomato Soup',
  description: 'A simple, warming tomato soup.',
  prepTimeMinutes: 10,
  cookTimeMinutes: 20,
  servings: 4,
  parts: [],
  favsCount: 0,
  createdAt: new Date().toISOString(),
  author: { id: 'author-1', username: 'chef', name: 'Chef' },
};

describe('RecipeCard', () => {
  let component: RecipeCard;
  let fixture: ComponentFixture<RecipeCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecipeCard],
      // Injects Router directly.
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(RecipeCard);
    // `recipe` is a required input - must be set before the first change
    // detection pass or Angular throws NG0950.
    fixture.componentRef.setInput('recipe', mockRecipe);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
