import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      // App's template uses RouterLink/RouterOutlet and injects Router
      // directly - both need a router context to construct.
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the toolbar brand', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.toolbar-brand')?.textContent).toContain('Recipes');
  });

  it('should show guest nav links when signed out', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    // UserService.isAuthenticated defaults to false with no token stored -
    // the toolbar should offer Sign In / Register, not the profile menu.
    expect(compiled.textContent).toContain('Sign In');
    expect(compiled.textContent).toContain('Register');
    expect(compiled.textContent).not.toContain('Logout');
  });
});
