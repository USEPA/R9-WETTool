import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { RootComponent } from './root.component';
import {RouterTestingModule} from '@angular/router/testing';
import {HttpClientTestingModule} from '@angular/common/http/testing';
import {MatSnackBar} from '@angular/material/snack-bar';
import {LoadingService} from '../shared/services/loading.service';
import {TitleService} from '../services/title.service';

describe('RootComponent', () => {
  let component: RootComponent;
  let fixture: ComponentFixture<RootComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule, HttpClientTestingModule],
      declarations: [ RootComponent ],
      providers: [
        {provide: MatSnackBar, useValue: {}},
        {provide: 'env', useValue: {}},
        LoadingService,
        TitleService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RootComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
