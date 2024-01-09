import {TestBed} from '@angular/core/testing';

import {MapService} from './map.service';

let service: MapService;

describe('MapService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MapService
      ]
    });
    service = new MapService([]);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
