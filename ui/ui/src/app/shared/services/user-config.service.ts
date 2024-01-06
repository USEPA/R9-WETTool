import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, ReplaySubject} from 'rxjs';
import {tap} from 'rxjs/operators';

interface UserConfig {
  name: string;
  permissions: string[];
  is_superuser: boolean;
  groups: string[];
  config: {
    default_webmap: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class UserConfigService {
  config: ReplaySubject<any> = new ReplaySubject<UserConfig>();
  base_map_id: ReplaySubject<string> = new ReplaySubject<string>();
  private current_config: UserConfig = {
    name: '',
    permissions: [],
    is_superuser: false,
    groups: [],
     config: {default_webmap:''}
  };
  constructor(public http: HttpClient) {
    this.config.subscribe(config => this.current_config = config);
  }

  loadConfig(): Observable<any> {
    return this.http.get(`/current_user/`).pipe(
      tap(config => this.config.next(config))
    );
  }

  checkGroups(groups: string[]) {
    if (this.current_config.is_superuser) {
      return true;
    }
    for (const group of groups) {
      if (this.current_config.groups.includes(group)) {
        return true;
      }
    }
    return false;
  }

  checkPermissions(permission: string) {
    return this.current_config.is_superuser ? this.current_config.is_superuser : this.current_config.permissions.includes(permission);
  }
}
