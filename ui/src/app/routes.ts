import {Routes, ResolveFn, ActivatedRouteSnapshot, RouterStateSnapshot} from '@angular/router';
import {HomeComponent} from './home/home.component';
import {QuestionListComponent} from './question-list/question-list.component';
import {QuestionDetailsComponent} from "./question-details/question-details.component";

// const resolvedTitle = 'asdf';
// const resolvedTitle: ResolveFn<string> = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {return inject(TitleService).getTitle()};

const routeConfig: Routes = [
  {
    path: '',
    component: HomeComponent,
    title: 'R9 WET Tool',
    // title: resolvedTitle
  },
  {
    path: 'questions',
    children: [
      { path:'',
        component: QuestionListComponent,
        title: 'Question List',
      },
      { path:':id',
        component: QuestionDetailsComponent,
        title: 'Question Details',
      }
    ]
  },
];

export default routeConfig;
