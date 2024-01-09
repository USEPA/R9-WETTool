import {Injectable} from '@angular/core';
import {Observable, ReplaySubject} from 'rxjs';
import {filter, map, switchMap, tap} from 'rxjs/operators';
import {project, load} from '@arcgis/core/geometry/projection';
import {geodesicBuffer} from '@arcgis/core/geometry/geometryEngine';

import Polygon from '@arcgis/core/geometry/Polygon';
import Geometry from '@arcgis/core/geometry/Geometry';
import LinearUnits = __esri.LinearUnits;

@Injectable({
  providedIn: 'root'
})
export class GeometryService {
  constructor() {
  }

  public bufferGeometry(geometry: Polygon, distance: number, units?: LinearUnits): Polygon {
    if (geometry !== null) {
      return geodesicBuffer(geometry, distance, units) as Polygon;
    }
    return null;
  }

  public project(geometry: Geometry, outSpatialReference: number): Observable<Geometry> {
    return new Observable(obs => {
      load().then(() => {
        obs.next(project(geometry, {wkid: outSpatialReference}) as Geometry);
        obs.complete();
      });
    });
  }
}
