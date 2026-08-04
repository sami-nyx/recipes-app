import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Authenticated } from './authenticated';

describe('Authenticated', () => {
  let component: Authenticated;
  let fixture: ComponentFixture<Authenticated>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Authenticated],
    }).compileComponents();

    fixture = TestBed.createComponent(Authenticated);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
