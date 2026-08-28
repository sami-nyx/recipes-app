import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { NotAuthenticated } from './not-authenticated';

describe('NotAuthenticated', () => {
  let component: NotAuthenticated;
  let fixture: ComponentFixture<NotAuthenticated>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NotAuthenticated],
      // Its template uses RouterLink.
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(NotAuthenticated);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
