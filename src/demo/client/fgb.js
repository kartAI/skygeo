document.addEventListener("DOMContentLoaded", async () => { 
    // basic OSM Leaflet map
  let map = L.map('map').setView([58.15, 8], 12);
    L.tileLayer('https://cache.kartverket.no/v1/wmts/1.0.0/topograatone/default/webmercator/{z}/{y}/{x}.png', {
        maxZoom: 18,
        minZoom: 10
    }).addTo(map);

    // optionally show some meta-data about the FGB file
    function handleHeaderMeta(headerMeta) {
        const header = document.getElementById('header')
        const formatter = new JSONFormatter(headerMeta, 10)
        while (header.firstChild)
            header.removeChild(header.firstChild)
        header.appendChild(formatter.render())
    }

    // For the example, we fix a visible Rect in the middle of the map
    function getBoundForRect() {
        const bounds = map.getBounds();

        const width = map.distance(bounds.getNorthWest(), bounds.getNorthEast());
        const height = map.distance(bounds.getNorthWest(), bounds.getSouthWest());
        return map.getCenter().toBounds(Math.min(width, height) * 0.8);
    }

    // convert the rect into the format flatgeobuf expects
    function fgBoundingBox() {
        const bounds = getBoundForRect();
        return {
            minX: bounds.getWest(),
            maxX: bounds.getEast(),
            minY: bounds.getSouth(),
            maxY: bounds.getNorth(),
        };
    }

    // show a leaflet rect corresponding to our bounding box
    let rectangle = L.rectangle(getBoundForRect(), { interactive: false, color: "blue", fillOpacity: 0.0, opacity: 1.0 }).addTo(map);

    // track the previous results so we can remove them when adding new results
    let previousResults = L.layerGroup().addTo(map);
    async function updateResults() {
        // remove the old results
        previousResults.remove();
        const nextResults = L.layerGroup().addTo(map);
        previousResults = nextResults;

        // Use flatgeobuf JavaScript API to iterate features as geojson.
        // Because we specify a bounding box, flatgeobuf will only fetch the relevant subset of data,
        // rather than the entire file.
    const iter = flatgeobuf.deserialize('http://localhost:8081/fgb/n50_samferdsel_senterlinje.fgb', fgBoundingBox(), handleHeaderMeta);

        const colorScale = ((d) => {
            return d > 750 ? '#800026' :
                d > 500 ? '#BD0026' :
                d > 250  ? '#E31A1C' :
                d > 100 ? '#FC4E2A' :
                d > 50   ? '#FD8D3C' :
                d > 25  ? '#FEB24C' :
                d > 10   ? '#FED976' :
                '#FFEDA0'
        });

        for await (const feature of iter) {
            // Leaflet styling
            console.log(feature)
            const defaultStyle = { 
                color: colorScale(feature.properties["sporantall"]), 
                weight: 1, 
                fillOpacity: 1,
            };
            L.geoJSON(feature)
      // , {
                // style: defaultStyle,
           //  }).on({
           //      'mouseover': function(e) {
           //          const layer = e.target;
           //          layer.setStyle({
           //              weight: 4,
           //              fillOpacity: 0.8,
           //          });
           //      },
           //      'mouseout': function(e) {
           //          const layer = e.target;
           //          layer.setStyle(defaultStyle);
           //      }
           // }).bindPopup(`${feature.properties["sporantall"]} people live in this census block.</h1>`)
           .addTo(nextResults);
        }
        rectangle.bringToFront();
    }
    // if the user is panning around alot, only update once per second max
    updateResults = _.throttle(updateResults, 1000);

    // show results based on the initial map
    updateResults();
    // ...and update the results whenever the map moves
    map.on("moveend", function(s){
        rectangle.setBounds(getBoundForRect());
        updateResults();
    });
});
