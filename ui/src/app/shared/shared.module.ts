import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RouterModule} from '@angular/router';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatDialogModule} from '@angular/material/dialog';
import {MatTableModule} from '@angular/material/table';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatMenuModule} from '@angular/material/menu';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatTooltipModule} from '@angular/material/tooltip';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {HttpClientModule} from '@angular/common/http';

import {LoadingService} from './services/loading.service';
import {UserConfigService} from './services/user-config.service';
// import {BreadcrumbService} from './breadcrumb/breadcrumb.service';

// import {BreadCrumbComponent} from './breadcrumb/breadcrumb.component';


@NgModule({
  declarations: [
    // BreadCrumbComponent,
  ],
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatSelectModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatMenuModule,
    MatInputModule,
    HttpClientModule,
    MatDialogModule,
    MatTableModule,
    MatPaginatorModule,
    MatCheckboxModule,
    MatTooltipModule,
    BrowserAnimationsModule
  ],
  providers: [
    // AuthService,
    UserConfigService,
    LoadingService,
    // BreadcrumbService
  ]
})
export class SharedModule { }
