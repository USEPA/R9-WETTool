import {TestBed, inject} from '@angular/core/testing';

import {BaseService} from './base.service';
import {SharedModule} from '../shared.module';
import {HttpClientTestingModule} from '@angular/common/http/testing';
import {LoadingService} from './loading.service';
import {HttpClient} from '@angular/common/http';

let service: BaseService;

describe('BaseService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
      ],
      providers: [
        LoadingService
      ]
    });
    let loadingService = TestBed.inject(LoadingService);
    let httpClient = TestBed.inject(HttpClient);
    service = new BaseService('', httpClient, loadingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
