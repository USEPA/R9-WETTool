import { Injectable } from '@angular/core';
import {Subject} from 'rxjs';

@Injectable()
export class TitleService {
  private titleStream: Subject<string> = new Subject();
  constructor() { }

  public setTitle(title: string) {
    this.titleStream.next(title);
  }

  public getTitle(): Subject<string> {
    return this.titleStream;
  }
}
