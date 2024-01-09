import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '', canActivateChild: [],
    // data: {
    //   type: 'ptt',
    //   message: 'PTT Group'
    // },
    children: [
      {path: '', redirectTo: 'dashboard', pathMatch: 'full'}
    ]
  }
]

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})


export class AppRoutingModule {
}
