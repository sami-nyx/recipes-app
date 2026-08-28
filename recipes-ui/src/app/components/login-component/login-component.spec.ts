import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { LoginComponent } from './login-component';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      // Injects Router directly and its template uses RouterLink.
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should be invalid when username or password is blank', () => {
    component.loginForm.patchValue({ usernameOrEmail: '', password: '' });
    expect(component.loginForm.invalid).toBe(true);
  });

  it('should require at least 6 characters for the password', () => {
    component.loginForm.patchValue({ usernameOrEmail: 'someone', password: '123' });
    expect(component.loginForm.get('password')?.hasError('minlength')).toBe(true);
  });

  it('should be valid with a username and a long-enough password', () => {
    component.loginForm.patchValue({ usernameOrEmail: 'someone', password: 'longenoughpass' });
    expect(component.loginForm.valid).toBe(true);
  });
});
