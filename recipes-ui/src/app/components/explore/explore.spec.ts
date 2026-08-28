import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Explore } from './explore';

describe('Explore', () => {
  let component: Explore;
  let fixture: ComponentFixture<Explore>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Explore],
      // Explore injects Router directly and its template pulls in
      // PersonalComponent, which needs a router context of its own.
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Explore);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
