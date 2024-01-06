import {Injectable} from '@angular/core';
import {ReplaySubject} from "rxjs";

export interface Breadcrumb {
  label: string;
  url?: string;
}

@Injectable()
export class BreadcrumbService {
  private breadcrumbStream: ReplaySubject<Breadcrumb[]> = new ReplaySubject();

  constructor() {
  }

  public setBreadcrumb(title: Breadcrumb[]) {
    this.breadcrumbStream.next(title);
  }

  public getBreadcrumb() {
    return this.breadcrumbStream;
  }
}
