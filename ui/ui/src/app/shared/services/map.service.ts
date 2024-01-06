import {map, switchMap, take, tap} from 'rxjs/operators';
import {forkJoin, Observable, ReplaySubject, Subject} from 'rxjs';
import {environment} from '../../../environments/environment';
import WebMap from '@arcgis/core/WebMap';
import MapView from '@arcgis/core/views/MapView';
import BasemapGallery from '@arcgis/core/widgets/BasemapGallery';
import AreaMeasurement2D from '@arcgis/core/widgets/AreaMeasurement2D';
import CoordinateConversion from '@arcgis/core/widgets/CoordinateConversion';
import ScaleBar from '@arcgis/core/widgets/ScaleBar';
import Fullscreen from '@arcgis/core/widgets/Fullscreen';
import Expand from '@arcgis/core/widgets/Expand';
import LayerList from '@arcgis/core/widgets/LayerList';
import Layer from '@arcgis/core/layers/Layer';
import FeatureLayer from '@arcgis/core/layers/FeatureLayer';
import MapImageLayer from '@arcgis/core/layers/MapImageLayer';
import Map from '@arcgis/core/Map';
import esriConfig from '@arcgis/core/config';
import {addProxyRule} from '@arcgis/core/core/urlUtils';
import PortalBasemapsSource from '@arcgis/core/widgets/BasemapGallery/support/PortalBasemapsSource';
import Portal from '@arcgis/core/portal/Portal';
import Legend from "@arcgis/core/widgets/Legend";

export class MapService {
  WebMap;
  MapView;
  MapImageLayer;
  FeatureLayer;
  Graphic;
  map: ReplaySubject<Map> = new ReplaySubject<Map>();
  view: ReplaySubject<MapView> = new ReplaySubject<MapView>();
  // genericLayer: GraphicsLayer;
  // initial_extent: Extent;
  _view: MapView;

  constructor(public map_services: string[]) {
  }

  async init(element_id: string, base_map_id: string): Promise<any> {
    const vm = this;
    // type MapModules = [
    //   WebMap, MapView, MapImageLayer, LayerList, config, urlUtils,
    //   any, Legend, BasemapGallery, Expand, GraphicsLayer, Graphic];
    // ]
    // const AUMLayerListType = await import('../widgets/AUMLayerList');

    // const [_WebMap, _MapView, _MapImageLayer, LayerList, esriConfig, urlUtils, all, Legend, BasemapGallery,
    //   Expand, GraphicsLayer, _Graphic, AreaMeasurement2D, ScaleBar, CoordinateConversion, Fullscreen, _FeatureLayer
    // ] = await (loadModules(['esri/WebMap', 'esri/views/MapView',
    //   'esri/layers/MapImageLayer', 'esri/widgets/LayerList', 'esri/config', 'esri/core/urlUtils', 'dojo/promise/all',
    //   'esri/widgets/Legend', 'esri/widgets/BasemapGallery', 'esri/widgets/Expand', 'esri/layers/GraphicsLayer',
    //   'esri/Graphic', 'esri/widgets/AreaMeasurement2D', 'esri/widgets/ScaleBar', 'esri/widgets/CoordinateConversion',
    //   'esri/widgets/Fullscreen', 'esri/layers/FeatureLayer']));

    esriConfig.request.trustedServers.push(environment.local_service_endpoint);

    environment.proxied_urls.forEach(url => addProxyRule({
        proxyUrl: `${environment.local_service_endpoint}/esri-proxy/`,
        urlPrefix: url
      })
    );

    // // addProxyRule({
    // //   urlPrefix: 'services.arcgis.com/cJ9YHowT8TU7DUyn',
    // //   proxyUrl: `${environment.local_service_endpoint}/esri-proxy/`,
    // // });
    // addProxyRule({
    //   urlPrefix: 'www.arcgis.com/sharing/rest',
    //   proxyUrl: `${environment.local_service_endpoint}/esri-proxy/`,
    // });

    const _map = await this.loadWebMap(base_map_id);

    vm._view = new MapView({
      map: _map,
      container: element_id,
    });

    // Create basemapGallery widget instance
    const basemapGallery = new BasemapGallery({
      view: vm._view,
      container: document.createElement('div'),
      source: {
        portal: new Portal({url: environment.portal_base_url})
      } as PortalBasemapsSource
    });
    // Create compass widget
    // const compass = new Compass({
    //   view: vm._view,
    //   container: document.createElement('div')
    // });
    // Create Measure Widget
    const measurementWidget = new AreaMeasurement2D({
      view: vm._view,
      container: document.createElement('measurementdiv'),
    });
    // vm._view.ui.add(measurementWidget, 'top-left');
    // measurementWidget.watch('viewModel.state', function (state) {
    //   setTimeout(function () {
    //     const button = query('.esri-area-measurement-3d__clear-button')[0];
    //     button.innerHTML = 'Area Measurement';
    //     domAttr.set(button, 'breadcrumbs', 'Area Measurement');
    //   }, 0);
    // });

    // Create ScaleBar widget
    const scaleBar = new ScaleBar({
      view: vm._view,
      container: document.createElement('div')
    });
    // Create coordinate conversion widget
    const ccWidget = new CoordinateConversion({
      view: vm._view,
      container: document.createElement('div')
    });
    const fullscreen = new Fullscreen({
      view: vm._view,
      // element: 'mapDiv'
    });


    // Create an Expand instance
    const bgExpand = new Expand({
      view: vm._view,
      content: basemapGallery
    });
    // close the expand whenever a basemap is selected
    basemapGallery.watch('activeBasemap', function () {
      const mobileSize = vm._view.heightBreakpoint === 'xsmall' || vm._view.widthBreakpoint === 'xsmall';

      if (mobileSize) {
        bgExpand.collapse();
      }
    });
    const widgetExpand = new Expand({
      view: vm._view,
      content: measurementWidget,
      // expandIconClass: 'esri-icon-measure-area',
    });

    // Add the expand instance to the ui
    vm._view.ui.add(bgExpand, 'top-left');
    // vm._view.ui.add(compass, 'bottom-left');
    vm._view.ui.add(ccWidget, 'bottom-right');
    // vm._view.ui.add(widgetExpand, 'top-left');
    vm._view.ui.add(scaleBar, 'bottom-right');
    vm._view.ui.add(fullscreen, 'top-left');


    const layerList = new LayerList({
      view: vm._view,
      listItemCreatedFunction: function (event) {
        const item = event.item;
        // if (item.parent === null) { // don't show legend twice
        item.panel = {
          content: 'legend',
          open: false
        };
        const actions = [
          // {
          //   breadcrumbs: 'Download Layerfile',
          //   className: 'esri-icon-download',
          //   id: 'download-layer'
          // }
        ];

        // if (item.breadcrumbs !== 'Main Mines Map') {
        //   actions.unshift({
        //     title: 'Remove Layer',
        //     className: 'esri-icon-close',
        //     id: 'remove-layer'
        //   });
        // }

        // item.actionsSections = [actions];
      }


      // }
    });

    layerList.on('trigger-action', (event) => {
      const id = event.action.id;
      if (id === 'remove-layer') {
        _map.remove(event.item.layer);
      } else if (id === 'download-layer') {
        console.log('layer file download not implemented');
      }
    });

    const legend = new Legend({view: vm._view});
    const legendExpand = new Expand({
      expandIconClass: 'esri-icon-legend',
      view: vm._view,
      content: legend
    });

    vm._view.ui.add([legendExpand, 'add-to-map-button'], 'top-right');

    vm._view.ui.add('save-map-button', 'bottom-right');
    // vm._view.ui.add('add-to-map-button', 'top-right');
    // vm.genericLayer = new GraphicsLayer({listMode: 'hide'});
    // setLayerProperty('highlight layer', 0, 'visible', false)
    // _map.add(vm.genericLayer);

    return vm._view.when(() => {
      vm.view.next(vm._view);
      // resolve();
    }, error => {
      console.log(error);
    });
  }


//
// addGraphics(geometries: any[], symbol: any) {
//   const vm = this;
//   this.map.pipe(
//     take(1),
//     tap(map => {
//       const graphics: Graphic[] = [];
//       geometries.forEach(geometry => {
//         graphics.push(new vm.Graphic({
//           geometry: geometry,
//           symbol: symbol
//         }))
//       });
//       vm.genericLayer.addMany(graphics);
//     })
//   ).subscribe();
// }
//
//
// clearGraphics() {
//   this.genericLayer.removeAll();
// }

  addLayers(map_services: any[]) {
    // let initial_extent;
    if (map_services !== undefined && map_services.length > 0) {
      const promises = [];
      let title;
      for (let service of map_services) {
        if (typeof service === 'object') {
          title = this.getServiceTitle(service);
          service = this.getServiceUrl(service);
        }
        promises.push(this.addLayer(service, title));
      }
      forkJoin(promises).subscribe();
      // trying to go to extent dynamically is problematic b/c of dealing with different projections
      // forkJoin(promises).subscribe((layers: Layer[]) => {
      // for (const layer of layers) {
      //   if (initial_extent === undefined) initial_extent = layer.fullExtent;
      //   else initial_extent.union(layer.fullExtent);
      // }
      // this._view.goTo(initial_extent).then(() => {
      //   this._view.goTo({zoom: this._view.zoom - 1});
      // });
      // });
    }
  }


  getServiceUrl(obj) {
    return obj.map_service_url;
  }

  getServiceTitle(obj) {
    let title = obj.title;
    if (!obj.title) {
      const index = obj.display_file_name.lastIndexOf('\\') + 1;
      title = obj.display_file_name.substring(index);
    }
    return title;
    // const index = obj.display_file_name.lastIndexOf('\\') + 1;
    // return obj.display_file_name.substring(index);
  }

// add layer using string
// add new layer but don't draw it

  addLayer(service: string | { url: string, title: string }, title ?: string):
    Observable<Layer> {
    let layer: any;
    return this.map.pipe(
      take(1),
      switchMap(_map => {
        const obs = new Subject<Layer>();
        const service_properties = typeof service === 'string' ? {url: service} : service;
        if (title) {
          service_properties['title'] = title;
        }
        // let layer: any;
        if (service_properties.url.includes('MapServer')) {
          layer = new MapImageLayer(service_properties);
        } else if (service_properties.url.includes('FeatureServer')) {
          layer = new FeatureLayer(service_properties);
        }

        _map.layers.add(layer, 10000);
        layer.when().then(() => {
          obs.next(layer);
          obs.complete();
        });
        return obs;
      }));
  }

  getLayer(service_name: string, index: number) {
    return this.map.pipe(take(1),
      map(_map => {
        const service: any = _map.allLayers.find(layer => {
          return layer.title === service_name;
        });
        return service.sublayers.find(layer => {
          return layer.id === index;
        });
      }));
  }

  getActiveLayer() {
    return this.map.pipe(take(1),
      switchMap(_map => {
        const loading = [];
        _map.layers.forEach(layer => loading.push(layer.when()));
        return forkJoin(loading);
      }),
      switchMap(() => this.map),
      map(_map => {
        return _map.layers.filter(layer => {
          return layer.visible && layer.listMode === 'show';
        });
      })
    );
  }

  setExtent(extent) {
    this.view.pipe(take(1),
      tap(view => view.extent = extent.expand(1.5)),
      // tap(view => this._view.goTo({zoom: this._view.zoom - 1}))
    ).subscribe();
  }

  setLayerProperty(service_name, index, property, value) {
    this.map.pipe(
      take(1),
      tap(_map => {
        const service: any = _map.allLayers.find(layer => {
          return layer.title === service_name;
        });
        if (service.sublayers) {
          const sublayer = service.sublayers.find(layer => {
            return layer.id === index;
          });
          sublayer[property] = value;
        } else {
          service[property] = value;
        }
      })).subscribe();
  }

  async loadWebMap(base_map_id): Promise<Map> {
    base_map_id = base_map_id ? base_map_id : environment.default_base_map;
    return new Promise((resolve => {
      if (base_map_id) {
        const _map = new WebMap({
          portalItem: {
            // id: vm.base_map_id ? vm.base_map_id : '886ed5fb3c8047d1af2e5613e64ba4ea'
            id: base_map_id
          }
        });
        _map.load().then(
          () => {
            this.map ? this.map.next(_map) : null;
            resolve(_map);
          },
          () => {
            this.loadWebMap(environment.default_base_map).then((__map) => resolve(__map));
          }
        );
      } else {
        const _map = new Map({
          basemap: 'satellite'
        });
        this.map.next(_map);
        resolve(_map);
      }

    }));
  }


}
