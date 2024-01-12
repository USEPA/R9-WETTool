import {HttpClient, HttpParams} from '@angular/common/http';
import {LoadingService} from './loading.service';
import {DataSource} from '@angular/cdk/collections';
import {finalize, map, tap} from 'rxjs/operators';
import {BehaviorSubject, Observable, ReplaySubject, Subject} from 'rxjs';
import {ActivatedRoute, ParamMap, Params, Router} from '@angular/router';

export interface SearchObject {
  search?: string;
  page?: any;
  page_size?: number | string;
  ordering?: string;
  object_id?: string | number;
  content_type?: any;

  // catch all
  [key: string]: any;
}

export interface Response {
  count: number;
  results: any[];
  content_type?: number;
}

interface FilterOptions {
  [key: string]: Observable<any>;
}

export class BaseService {
  currentPage: number = 1;
  count: number = 0;
  dataChange: BehaviorSubject<any[]> = new BehaviorSubject<any[]>([]);
  fullResponse: Subject<any> = new Subject<any>();
  filter: SearchObject;
  datasource: BaseDataSource;
  content_type = new ReplaySubject();
  filter_options: FilterOptions = {};
  assignedToValue = '';
  requestorValue = '';

  constructor(public base_url: string, public http: HttpClient, public loadingService: LoadingService,
              public dynamicFilterPaths: string[] = []) {
    this.datasource = new BaseDataSource(this);
    this.filter = {};
    this.getAllFilterOptions();
  }

  get data(): any[] {
    return this.dataChange.value;
  }

  getList(search_object: SearchObject = {}): Observable<Response> {
    const url = `/${this.base_url}`;
    return this.http.get<Response>(url,
      {
        params: Object.entries(search_object)
          .reduce((params, [key, value]) => params.set(key, value !== null ? value : ''), new HttpParams())
      }
    ).pipe(
      map(response => {
        if (response.hasOwnProperty('content_type')) {
          this.content_type.next(response.content_type);
          this.content_type.complete();
        }
        this.fullResponse.next(response);
        return response;
      })
    );
  }

  get(id: string | number) {
    return this.http.get<any>(`/${this.base_url}/${id}`);
  }

  put(id: string | number, item: object) {
    return this.http.put(`/${this.base_url}/${id}`, item);
  }

  post(item: object, httpOptions = {}): any {
    return this.http.post(`/${this.base_url}`, item, httpOptions).pipe(
      map(new_item => {
        const copiedData = this.data.slice();
        copiedData.unshift(new_item); // changed to unshift so it gets add to front of array for more visibility
        this.dataChange.next(copiedData);
        return new_item;
      })
    );
  }

  patch(id: string | number, partial_item: object) {
    return this.http.patch(`/${this.base_url}/${id}`, partial_item);
  }

  options() {
    return this.http.options<any>(`/${this.base_url}`);
  }

  getItems(): Observable<any[]> {
    this.loadingService.setLoading(true);
    return this.getList(this.filter).pipe(
      map(response => {
        this.currentPage = this.filter.page;
        this.count = response.count;
        this.dataChange.next(response.results);
        this.loadingService.setLoading(false);
        return response.results;
      })
    );
  }

  // getPage(event) {
  //   this.loadingService.setLoading(true);
  //   this.filter.page = event.pageIndex + 1;
  //   this.filter.page_size = event.pageSize;
  //   this.getItems().subscribe(() => this.loadingService.setLoading(false));
  // }

  runSearch() {
    this.loadingService.setLoading(true);
    this.filter.page = 1;
    this.getItems().pipe(
      tap(() => this.getAllFilterOptions()),
      finalize(() => this.loadingService.setLoading(false))
    ).subscribe();
  }

  clearSearch() {
    this.loadingService.setLoading(true);
    this.filter.search = '';
    this.getItems().pipe(
      tap(() => this.getAllFilterOptions()),
      finalize(() => this.loadingService.setLoading(false))
    ).subscribe();
  }

  // sortTable(event) {
  //   // this.loadingService.setLoading(true);
  //   this.filter.page = 1;
  //   const direction = event.direction === 'desc' ? '-' : '';
  //   this.filter.ordering = event.direction ? `${direction}${event.active}` : '';
  //   this.getItems()
  //     .subscribe(() => this.loadingService.setLoading(false));
  // }

  delete(id: string | number) {
    return this.http.delete(`/${this.base_url}/${id}`)
      .pipe(
        map(() => {
          const copiedData = this.data.slice();
          const filteredData = copiedData.filter(item => item.id !== id);
          this.dataChange.next(filteredData);
        })
      );
  }

  // accepts a path to query endpoint inside current base_url to get dynamic filter options
  // see mines/views.py trusts function; results available at /api/mine/sites/trusts
  getFilterOptions(path: string) {
    return this.http.get<any[]>(`/${this.base_url}/${path}`, {
      params: Object.entries(this.filter).reduce((params, [key, value]) => params.set(key, value !== null ? value : ''), new HttpParams())
    });
  }

  getAllFilterOptions() {
    for (const path of this.dynamicFilterPaths) {
      this.filter_options[path] = this.getFilterOptions(path);
    }
  }

  clearFilter(field:string): void {
    delete this.filter[field];
    this.getAllFilterOptions();
  }

  clearAllFilters(): void {
    for (const key in this.filter) {
      if (key !== 'page' && key !== 'page_size' && key !== 'search') {
        delete this.filter[key];
      }
    }
    this.getItems().pipe(
      tap(() => this.getAllFilterOptions()),
      finalize(() => this.loadingService.setLoading(false))
    ).subscribe();
  }

  public updateQueryParams(queryParam: Params, router: Router, route: ActivatedRoute): void {
    // remove highlight so it only happens once
    if (queryParam['highlight']) {
      queryParam['highlight'] = null;
    }
    if (router) {
      router.navigate(
        [],
        {relativeTo: route, queryParams: queryParam, replaceUrl: true}
      );
    }
  }

  public applyQueryParams(params: ParamMap): ParamMap {
    for (const key of params.keys) {
      // tslint:disable-next-line:radix
      const value = parseInt(<string>params.get(key));
      this.filter[key] = value ? value : params.get(key);
      if (key.includes('__in')) {
        const values = params.get(key)!.split(',');
        if (values.map(x => +x).some(isNaN)) {
          this.filter[key] = values;
        } else {
          this.filter[key] = values.map(x => +x);
        }
      }
      if (params.get(key) === 'true') { this.filter[key] = true; }
      if (params.get(key) === 'false') { this.filter[key] = false; }
    }
    return params;
  }
}

export class BaseDataSource extends DataSource<any> {
  constructor(private _projectDatabase: BaseService) {
    super();
  }

  connect(): Observable<any[]> {
    return this._projectDatabase.dataChange;
  }

  disconnect() {
  }
}
