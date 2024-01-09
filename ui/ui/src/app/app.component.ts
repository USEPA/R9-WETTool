import {Component, OnDestroy, OnInit} from '@angular/core';
import {Router} from '@angular/router';
// import {AuthService} from 'src/app/shared/services/auth.service';
import {UserConfigService} from 'src/app/shared/services/user-config.service';
import {Subscription} from 'rxjs';
import {tap} from 'rxjs/operators';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'R9 WET Tool';
  headerTitle = 'R9 Water Emergency Team Tool';
  userConfigSubscription: Subscription = this.userConfig.config.subscribe();

  constructor(private router: Router,
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
