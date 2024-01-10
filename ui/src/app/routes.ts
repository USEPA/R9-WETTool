import {Routes} from '@angular/router';
import {AppComponent} from "./app.component";
import {HomeComponent} from './home/home.component';
import {QuestionlistComponent} from "./questionlist/questionlist.component";
import {UserConfigService} from "./shared/services/user-config.service";

const routeConfig: Routes = [
  {
    path: '',
    component: HomeComponent,
    title: 'R9 WET Tool',
  },
  {
    path: 'home',
    component: HomeComponent,
    title: 'Home'
  },
  {
    path: 'questions',
    component: QuestionlistComponent,
    title: 'Question List',
    children: [
      // {
      //   path:'/:id',
      //   component: QuestionDetialComponnent,
      //   title: 'Question Details',
      // }
    ]
  }
];

export default routeConfig;
