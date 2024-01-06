import {Component, OnInit} from '@angular/core';
import {LoadingService} from '../shared/services/loading.service';
import {TitleService} from '../shared/services/title.service';
import {UserConfigService} from '../shared/services/user-config.service';
import {Router} from '@angular/router';
import {filter, switchMap, tap} from 'rxjs/operators';
import {Observable} from 'rxjs';
import {environment} from '../../environments/environment';
import {Title} from '@angular/platform-browser';

@Component({
  selector: 'root-state',
  templateUrl: './root.component.html',
  styleUrls: ['./root.component.css']
})
export class RootComponent implements OnInit {
  loading: boolean = false;
  // title: Observable<string>;
  // title: Observable<string> = this.titleService.getTitle();
  // config: UserConfig;
  // public user: Observable<UserConfig>;
  public user: Observable<any> = this.userConfigService.loadConfig();
  public admin_url = environment.admin_url;
  constructor(public router: Router, public loadingService: LoadingService, public userConfigService: UserConfigService,
              public titleService: TitleService, private browserTitleService: Title) {
  }

  ngOnInit() {
    if (this.router.url === '') {
      this.router.navigate(['dashboard']);
    }

    this.loadingService.getLoadingStream().subscribe(value => {
      setTimeout(() => this.loading = value);
    });

    // this.title = this.titleService.getTitle().pipe(
    //   tap(title => this.browserTitleService.setTitle(`DMT - ${title}`)),
    // );
    //
    // this.user = this.userConfigService.config.pipe(
    //   filter(c => c !== null)
    // );
  }

  // logout(): void {
  //   this.authService.logout().pipe(
  //     switchMap(() => this.router.navigate(['login']))
  //   ).subscribe();
  // }
}
