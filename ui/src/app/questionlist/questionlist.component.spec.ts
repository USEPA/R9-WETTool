import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuestionlistComponent } from './questionlist.component';

describe('QuestionlistComponent', () => {
  let component: QuestionlistComponent;
  let fixture: ComponentFixture<QuestionlistComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
    declarations: [QuestionlistComponent]
});
    fixture = TestBed.createComponent(QuestionlistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
