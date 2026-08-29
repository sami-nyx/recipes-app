import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UserBioComponent } from './user-bio-component';

describe('UserBioComponent', () => {
  let component: UserBioComponent;
  let fixture: ComponentFixture<UserBioComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserBioComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UserBioComponent);
    // `authorId` is a required input - must be set before the first change
    // detection pass or Angular throws NG0950.
    fixture.componentRef.setInput('authorId', 'author-1');
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
