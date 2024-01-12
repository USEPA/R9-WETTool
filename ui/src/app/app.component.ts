import {CommonModule} from '@angular/common';
import {Component, OnDestroy, OnInit} from '@angular/core';
import {RouterLinkActive, RouterLink, RouterOutlet, RouterModule} from '@angular/router';
import {HttpClient, HttpClientXsrfModule} from '@angular/common/http';
import {MatMenuModule} from '@angular/material/menu';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';
import {MatListModule} from '@angular/material/list';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {Subscription} from 'rxjs';

// import {AuthService} from 'src/app/shared/services/auth.service';
import {UserConfigService} from 'src/app/shared/services/user-config.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    HttpClientXsrfModule,
    MatSidenavModule,
    MatMenuModule,
    MatToolbarModule,
    MatButtonModule,
    MatListModule,
    MatIconModule,
    MatProgressSpinnerModule,
    // HomeComponent,
  ]
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'R9 WET Tool';
  headerTitle = 'R9 Water Emergency Team Tool';
  userConfigSubscription: Subscription = this.userConfig.config.subscribe();

  constructor(
              // private router: Router,
              // public authService: AuthService,
              public userConfig: UserConfigService
  ) {

  }

  ngOnInit() {
    // this.userConfigSubscription = this.userConfig.config.pipe(
    //   tap(c => console.log(c))
    // ).subscribe();
  }

  ngOnDestroy(): void {
    if (this.userConfigSubscription) { this.userConfigSubscription.unsubscribe(); }
  }

  logout() {
    console.log('not implemented yet');
    // this.loginService.logout().pipe(tap(() => this.router.navigate(['login']))).subscribe();
  }
}
