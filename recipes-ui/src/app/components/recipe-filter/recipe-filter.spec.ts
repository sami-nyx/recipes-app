import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RecipeFilterComponent } from './recipe-filter';

describe('RecipeFilter', () => {
  let component: RecipeFilterComponent;
  let fixture: ComponentFixture<RecipeFilterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecipeFilterComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(RecipeFilterComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
