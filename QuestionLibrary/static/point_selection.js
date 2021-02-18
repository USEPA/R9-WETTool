(function ($) {
    document.addEventListener('DOMContentLoaded', () => {
        var csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;

        // Load the Map and MapView modules
        require(["esri/Map", "esri/views/MapView", "esri/widgets/Sketch", "esri/layers/FeatureLayer",
                "esri/layers/GraphicsLayer", "esri/Graphic", "esri/geometry/projection", "esri/geometry/Point",
                "esri/layers/VectorTileLayer", 'esri/core/urlUtils', 'esri/config', "esri/widgets/Fullscreen",
                "esri/widgets/FeatureTable", "esri/widgets/Popup", "esri/widgets/LayerList", "esri/widgets/Expand"],
            function (Map, MapView, Sketch, FeatureLayer, GraphicsLayer, Graphic, projection, Point, VectorTileLayer,
                      urlUtils, esriConfig, Fullscreen, FeatureTable, Popup, LayerList, Expand) {
                esriConfig.request.trustedServers.push(host);
                urlUtils.addProxyRule({
                    urlPrefix: 'services.arcgis.com/cJ9YHowT8TU7DUyn',
                    proxyUrl: host + '/proxy/'
                });
                esriConfig.request.interceptors.push({
                    urls: ['https://services.arcgis.com/cJ9YHowT8TU7DUyn'],
                    headers: {
                        "X-CSRFToken": csrf
                    }
                });
                var tempGraphicsLayer = new GraphicsLayer();
                tempGraphicsLayer.listMode = 'hide';
                var references = new VectorTileLayer("https://www.arcgis.com/sharing/rest/content/items/af6063d6906c4eb589dfe03819610660/resources/styles/root.json");
                references.listMode = 'hide';
                var base_service = document.getElementById('id_base_map_service').value;
                const fl_node = document.getElementById('id_layer');

                var editGraphic;
                var allFeatures = [];
                let flayers = [];
                let fl;
                let view;
                parseLayers();
                renderMap();

                // Create a MapView instance (for 2D viewing) and reference the map instance
                fl_node.onchange = changeFeatureLayer;
                function changeFeatureLayer() {
                    // update focus fl
                    // redraw map, clear selection (get current)
                    // redraw table
                    renderMap();
                }
                function renderMap() {
                    if (document.getElementById('id_base_map_service').value) {
                        let fl = flayers[fl_node.options.selectedIndex];
                        // var fl = new FeatureLayer({
                        //     url: base_service + "/1"
                        // });

                        // Create a Map instance
                        const mapDiv = document.getElementById('mapDiv');
                        mapDiv.innerHTML = "";
                        var myMap = new Map({
                            basemap: 'satellite',
                            layers:  flayers.concat([references, tempGraphicsLayer])
                        });
                        view = new MapView({
                            map: myMap,
                            container: 'mapDiv'
                        });
                        fl.when(function () {
                            view.extent = fl.fullExtent;
                            getFeatures(fl);
                        });
                        var layerlist = new LayerList({
                          view: view,
                            // listItemCreatedFunction: function(event) {
                            //   var item = event.item;
                            //   item.title = item.title.replace('WET_Tool_BASE', '');
                            // }
                        });
                        const layerListExpand = new Expand({
                            expandIconClass: "esri-icon-layer-list",
                            view: view,
                            content: layerlist
                        });
                        view.ui.add(layerListExpand, "top-left");

                        const sketch = new Sketch({
                            layer: tempGraphicsLayer,
                            view: view,
                            availableCreateTools: ["polygon", "rectangle", "circle"]
                            // graphic will be selected as soon as it is created
                            //creationMode: "update"
                        });

                        /* once FeatureTable has more features and is out of beta it might be worth it
                        const featureTable = new FeatureTable({
                          view: view, // The view property must be set for the select/highlight to work
                          layer: fl,
                          container: "featuresTable"
                        });*/

                        sketch.on('update', e => {
                            $('#mapDiv button:not([type])').attr('type', 'button');
                            if (e.state === 'complete' && !e.aborted) {
                                selectFeaturesByGeometry(e.graphics[0].geometry, false);
                                selectFeaturesByGeometry(e.graphics[0].geometry, true);
                            }
                        });
                        sketch.on('create', e => {
                            if (e.state === 'complete') {
                                selectFeaturesByGeometry(e.graphic.geometry, false);
                            }
                        });
                        sketch.on('delete', e => {
                            selectFeaturesByGeometry(e.graphics[0].geometry, true);
                        });
                        const fullscreen = new Fullscreen({
                            view: view
                        });
                        view.ui.add(sketch, "top-right");
                        view.on("immediate-click", event => {
                            view.hitTest(event).then(response => {
                                const candidate = response.results.find(result => {
                                    return (
                                        result.graphic &&
                                        result.graphic.layer &&
                                        result.graphic.layer === fl
                                    );
                                });
                                // Select the rows of the clicked feature
                                var current_selection = getCurrentSelection();
                                var remove = current_selection.includes(candidate.graphic.attributes.OBJECTID);
                                candidate && selectFeatures([candidate.graphic.attributes.OBJECTID], remove);
                            });
                        });
                        view.when(function () {
                            $('#mapDiv button:not([type])').attr('type', 'button');
                            //$('#featuresTable button:not([type])').attr('type', 'button');
                            // apears to select by objectid
                            //featureTable.selectRows([336, 326]);
                        });
                        view.whenLayerView(fl).then(layerView => console.log(layerView));
                    }
                }




                var gridOptions;

                function parseLayers() {
                    flayers = [];
                    for (let i=0; i<fl_node.options.length; i++){
                        const ii = (i).toString();
                        const f = new FeatureLayer({
                            url: base_service + "/"+ii,
                            title: fl_node.options[i].innerText
                        });
                        flayers.push(f);
                    }
                //     todo - update layer list
                }

                function getFeatures(featureLayer) {
                    featureLayer.queryFeatures({"where": "1=1", "outFields": "*"}).then(function (featureSet) {
                        // todo: deal with getting more features if max returned
                        allFeatures = allFeatures.concat(featureSet.features);
                        var features = featureSet.features.map(f => f.attributes);
                        // todo - remove unnecessary fields from Base Inventory if Base Inventory
                        var columnDefs = featureSet.fields
                        //.filter(f => ! ['OBJECTID','created_date', 'created_user', 'last_edited_user', 'last_edited_date'].includes(f.name))
                            .map(f => {
                                var columnDef = {"headerName": f.alias, "field": f.name};
                                if (['OBJECTID', 'created_date', 'created_user', 'last_edited_user', 'last_edited_date'].includes(f.name)) {
                                    columnDef['hide'] = true;
                                }
                                return columnDef;
                            });
                        gridOptions = {
                            defaultColDef: {
                                flex: 1,
                                sortable: true,
                                filter: true,
                                floatingFilter: true,
                            },
                            rowSelection: 'multiple',
                            rowMultiSelectWithClick: true,
                            columnDefs: columnDefs,
                            rowData: features,
                            onFirstDataRendered: function (e) {
                                e.columnApi.autoSizeAllColumns();
                                highlightFeatures();
                            },
                            onRowClicked: function (e) {
                                selectFeatures([e.node.data.OBJECTID], !e.node.isSelected());
                            }
                        };
                        let gridDiv = document.querySelector('#featuresTable');
                        gridDiv.innerHTML = "";
                        let aGrid = new agGrid.Grid(gridDiv, gridOptions);

                    });

                }

                function selectFeaturesByGeometry(geometry, remove) {
                    flayers[fl_node.options.selectedIndex].queryObjectIds({geometry, spatialRelationship: 'contains'}).then(function (ids) {
                        selectFeatures(ids, remove);
                    });
                }

                function selectFeatures(ids, remove) {
                    var current_selection = getCurrentSelection();
                    var new_selection = remove ? current_selection.filter(id => !ids.includes(id)): new Set(current_selection.concat(ids));
                    document.getElementById('id_selected_features').value = [...new_selection].join(',');
                    highlightFeatures();
                }

                var highlight;
                function highlightFeatures() {
                    var current_selection = getCurrentSelection();
                    gridOptions.api.forEachNode(function (node) {
                        node.setSelected(current_selection.includes(node.data.OBJECTID));
                    });

                    view.whenLayerView(flayers[fl_node.options.selectedIndex]).then(layerView => {
                        if (highlight) {
                            highlight.remove();
                        }
                        var selected_features = allFeatures.filter(f => current_selection.includes(f.attributes.OBJECTID))
                        highlight = layerView.highlight(selected_features);
                    });
                }

                function getCurrentSelection() {
                    return document.getElementById('id_selected_features').value
                        .split(',')
                        .filter(id => id !== "")
                        .map(id => parseInt(id, 10));
                }
            });
    });
})(django.jQuery);