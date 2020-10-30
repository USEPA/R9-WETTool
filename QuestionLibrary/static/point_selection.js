(function ($) {
    document.addEventListener('DOMContentLoaded', () => {
        var csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;

        // Load the Map and MapView modules
        require(["esri/Map", "esri/views/MapView", "esri/widgets/Sketch", "esri/layers/FeatureLayer",
                "esri/layers/GraphicsLayer", "esri/Graphic", "esri/geometry/projection", "esri/geometry/Point", "esri/layers/VectorTileLayer",
                'esri/core/urlUtils', 'esri/config', "esri/widgets/Fullscreen", "esri/widgets/FeatureTable"],
            function (Map, MapView, Sketch, FeatureLayer, GraphicsLayer, Graphic, projection, Point, VectorTileLayer,
                      urlUtils, esriConfig, Fullscreen, FeatureTable) {
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
                var references = new VectorTileLayer("https://www.arcgis.com/sharing/rest/content/items/af6063d6906c4eb589dfe03819610660/resources/styles/root.json");

                var editGraphic;
                var allFeatures = [];

                //var projectionPromise = projection.load();

                // Create a MapView instance (for 2D viewing) and reference the map instance


                if (document.getElementById('id_base_map_service').value) {
                    var base_service = document.getElementById('id_base_map_service').value;
                    // {# todo: figure out how to id the correct layer #}
                    var fl = new FeatureLayer({
                        url: base_service + "/1"
                    })
                    // Create a Map instance
                    var myMap = new Map({
                        basemap: 'satellite',
                        layers: [references, fl, tempGraphicsLayer]
                    });
                    var view = new MapView({
                        map: myMap,
                        container: 'mapDiv'
                    });
                    fl.when(function () {
                        view.extent = fl.fullExtent;
                        getFeatures();
                    });
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
                        $('#mapDiv button:not([type])').attr('type', 'button')
                        if (e.state === 'complete' && !e.aborted) {
                            selectFeaturesByGeometry(e.graphics[0].geometry, false);
                        }
                    });
                    sketch.on('create', e => {
                        if (e.state === 'complete') {
                            selectFeaturesByGeometry(e.graphic.geometry, false);
                        }
                    })
                    sketch.on('delete', e => {
                        selectFeaturesByGeometry(e.graphics[0].geometry, true);
                    })
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

                var gridOptions;

                function getFeatures() {
                    fl.queryFeatures({"where": "1=1", "outFields": "*"}).then(function (featureSet) {
                        // todo: deal with getting more features if max returned
                        allFeatures = allFeatures.concat(featureSet.features);
                        var features = featureSet.features.map(f => f.attributes);
                        var columnDefs = featureSet.fields
                        //.filter(f => ! ['OBJECTID','created_date', 'created_user', 'last_edited_user', 'last_edited_date'].includes(f.name))
                            .map(f => {
                                var columnDef = {"headerName": f.alias, "field": f.name};
                                if (['OBJECTID', 'created_date', 'created_user', 'last_edited_user', 'last_edited_date'].includes(f.name)) {
                                    columnDef['hide'] = true
                                }
                                return columnDef;
                            })
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
                                selectFeatures([e.node.data.OBJECTID], !e.node.isSelected())
                            }
                        }
                        var gridDiv = document.querySelector('#featuresTable');
                        new agGrid.Grid(gridDiv, gridOptions);

                    });

                }

                function selectFeaturesByGeometry(geometry, remove) {
                    fl.queryObjectIds({geometry, spatialRelationship: 'contains'}).then(function (ids) {
                        selectFeatures(ids, remove);
                    });
                }

                function selectFeatures(ids, remove) {
                    var current_selection = getCurrentSelection();
                    if (remove) {
                        var new_selection = current_selection.filter(id => !ids.includes(id))
                    } else {
                        var new_selection = new Set(current_selection.concat(ids));
                    }
                    document.getElementById('id_selected_features').value = [...new_selection].join(',');
                    highlightFeatures();
                }

                var highlight;

                function highlightFeatures() {
                    var current_selection = getCurrentSelection();
                    gridOptions.api.forEachNode(function (node) {
                        node.setSelected(current_selection.includes(node.data.OBJECTID));
                    });

                    view.whenLayerView(fl).then(layerView => {
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
                        .map(id => parseInt(id, 10))
                }

            });
    });
})(django.jQuery);