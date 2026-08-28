import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ViewRecipeComponent } from './view-recipe-component';

describe('ViewRecipeComponent', () => {
  let component: ViewRecipeComponent;
  let fixture: ComponentFixture<ViewRecipeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewRecipeComponent],
      // Reads the "id" route param via ActivatedRoute.snapshot and
      // injects Router directly.
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ViewRecipeComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
