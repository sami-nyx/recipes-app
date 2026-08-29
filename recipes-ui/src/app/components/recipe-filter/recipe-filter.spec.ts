import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RecipeFilterComponent } from './recipe-filter';
import { RecipeFilter } from '../../models/recipe-filter.model';

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

  it('should include the contributor in the emitted filter', () => {
    let emitted: RecipeFilter | undefined;
    component.filterChange.subscribe((filter) => (emitted = filter));

    component.contributor.set('sami_cooks');
    component.onFilterUpdated();

    expect(emitted?.contributor).toBe('sami_cooks');
  });

  it('should clear the contributor on reset, along with everything else', () => {
    component.searchQuery.set('tofu');
    component.contributor.set('sami_cooks');

    component.resetFilters();

    expect(component.contributor()).toBe('');
    expect(component.searchQuery()).toBe('');
  });
});
