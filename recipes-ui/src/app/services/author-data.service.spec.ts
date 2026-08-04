import { TestBed } from '@angular/core/testing';

import { AuthorDataService } from './author-data.service';

describe('UserDataService', () => {
  let service: AuthorDataService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthorDataService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
