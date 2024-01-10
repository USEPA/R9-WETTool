import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {CommonModule} from '@angular/common';
import {RouterModule} from '@angular/router';
import {HttpClientXsrfModule} from '@angular/common/http';
import {MatMenuModule} from '@angular/material/menu';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';
import {MatListModule} from '@angular/material/list';
import {MatIconModule} from "@angular/material/icon";
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';

import {environment} from '../environments/environment';
import {TitleService} from './shared/services/title.service';

import {AppRoutingModule} from './app-routing.module';
import {SharedModule} from './shared/shared.module';
import {AppComponent} from './app.component';
import {HomeComponent} from './home/home.component';



@NgModule({
  declarations: [
    AppComponent,
    HomeComponent
  ],
  imports: [
    BrowserModule,
    CommonModule,
    SharedModule,
    RouterModule,
    AppRoutingModule,
    MatSidenavModule,
    MatMenuModule,
    MatToolbarModule,
    MatButtonModule,
    MatListModule,
    MatIconModule,
    MatProgressSpinnerModule,
    HttpClientXsrfModule.withOptions({cookieName: environment.csrfCookieName, headerName: 'X-CSRFToken'}),
  ],
  providers: [
    TitleService,
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
