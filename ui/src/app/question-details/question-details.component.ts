import {Component, Input} from '@angular/core';
import {CommonModule} from "@angular/common";
import {ActivatedRoute} from '@angular/router';
import {HttpClient} from '@angular/common/http';
import {FormControl, FormGroup, ReactiveFormsModule} from '@angular/forms';
import {Observable} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {BaseService} from '../shared/services/base.service';
import {LoadingService} from '../shared/services/loading.service';
import {environment} from '../../environments/environment';
import {Question} from "../question";

@Component({
  selector: 'app-question-detials',
  templateUrl: './question-details.component.html',
  styleUrls: ['./question-details.component.scss'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule]
})

export class QuestionDetailsComponent {
  routed_id: number = 0;
  question$!: any;
  questionService: BaseService;
  questionDetailForm = new FormGroup({
    question: new FormControl('')
  })

  constructor(
    private route: ActivatedRoute,
    public http: HttpClient,
    public loading: LoadingService
  ) {
    this.routed_id = parseInt(this.route.snapshot.params['id'], 10);
    this.questionService = new BaseService(`api/question`, http, loading);
    this.questionService.get(this.routed_id).subscribe((q: Question) => this.question$ = q);
  }

  ngOnInit(){
    // this.question$ = this.route.paramMap.pipe(
    //   switchMap(params => {
    //      this.routed_id = Number(params.get('id'));
    //      return this.questionService.get(this.routed_id);
    //   })
    // )
  }


}
