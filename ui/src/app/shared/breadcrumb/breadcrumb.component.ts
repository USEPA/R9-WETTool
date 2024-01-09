import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, NavigationEnd, Router} from "@angular/router";
import {distinctUntilChanged, filter, map, switchMap} from "rxjs/operators";
import {Breadcrumb, BreadcrumbService} from "../services/breadcrumb.service";

@Component({
  selector: 'app-breadcrumb',
  templateUrl: './breadcrumb.component.html',
  styleUrls: ['./breadcrumb.component.css']
})
export class BreadcrumbComponent implements OnInit {
  breadcrumbs;

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {

    // this.breadcrumbs = this.activatedRoute.data.pipe(
    //   map(data => {
    //     console.log(data.breadcrumbs)
    //     return data.breadcrumbs;
    //   })
    // );
    // this.breadcrumbs = this.router.events.pipe(
    //   filter(event => event instanceof NavigationEnd),
    //   map(event => {
    //     console.log(this.activatedRoute);
    //    return  this.activatedRoute;
    //   }),
    //   // map(data => data.breadcrumbs)
    // );
  }

  // buildBreadCrumb(route: ActivatedRoute,
  //                 breadcrumbs: Array<BreadCrumb> = []): Array<BreadCrumb> {
  //   if (route.routeConfig && route.routeConfig.data && route.routeConfig.data.hasOwnProperty('breadcrumb')) {
  //     // If no routeConfig is avalailable we are on the root path
  //     const label = route.routeConfig ? route.routeConfig.data['breadcrumb'] : 'Home';
  //     const path = route.routeConfig ? route.routeConfig.path : 'home';
  //     // In the routeConfig the complete path is not available,
  //     // so we rebuild it each time
  //     const nextUrl = `${path}/`;
  //     const breadcrumb = {
  //       label: label,
  //       url: nextUrl,
  //     };
  //     const newBreadcrumbs = [...breadcrumbs, breadcrumb];
  //     if (route.firstChild) {
  //       // If we are not on our current path yet,
  //       // there will be more children to look after, to build our breadcumb
  //       return this.buildBreadCrumb(route.firstChild, newBreadcrumbs);
  //     }
  //     return newBreadcrumbs;
  //   } else {
  //     return this.buildBreadCrumb(route.firstChild);
  //   }
  // }

}
