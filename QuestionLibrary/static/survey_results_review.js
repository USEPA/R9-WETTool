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


                if (document.getElementById('id_survey123_service').value) {
                    var base_service = document.getElementById('id_survey123_service').value;
                    // {# todo: figure out how to id the correct layer #}
                    var fl = new FeatureLayer({
                        url: base_service
                    });
                    // Create a Map instance
                    // fl.when(function () {
                    //     view.extent = fl.fullExtent;
                    //     getFeatures();
                    // });
                    getFeatures();

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
                            var gridDiv = document.querySelector('#featuresReviewTable');
                            new agGrid.Grid(gridDiv, gridOptions);

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

                }
            });
    });
})(django.jQuery);