import { TestBed } from '@angular/core/testing';

import { UserConfigService } from './user-config.service';
import {SharedModule} from '../shared.module';
import {HttpClientTestingModule} from '@angular/common/http/testing';
import {MatSnackBarModule} from '@angular/material/snack-bar';

describe('UserConfigService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [
      SharedModule,
      HttpClientTestingModule,
      MatSnackBarModule
    ]
  }));

  it('should be created', () => {
    const service: UserConfigService = TestBed.get(UserConfigService);
    expect(service).toBeTruthy();
  });
});
