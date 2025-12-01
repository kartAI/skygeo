document.addEventListener("DOMContentLoaded", async () => {
    // Enable file bar
    const bar = document.getElementById('fileBar');
    const fs = document.getElementById('fileSize');
    const barWidth = bar.clientWidth;

    const filePath = "n250_samferdsel_senterlinje.fgb"

    let cl = null;
    const fileHead = fetch(
        filePath,
        { method: 'HEAD' }
    ).then(fh => {
        cl = fh.headers.get('content-length');
        fs.textContent = `${Number(cl / 1024 / 1024, 2).toFixed(2)} MB`
    })

    // Register the Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').then(() => {
            console.log('[main] Service Worker registered.');
        });

        // Listen for messages from the SW
        navigator.serviceWorker.addEventListener('message', event => {
            const data = event.data;
            if (data?.type === 'range-log') {
                if (data.start && data.end) {
                    const left = Math.ceil((data.start / cl) * barWidth);
                    const width = Math.ceil(((data.end - data.start) / cl) * barWidth);

                    const rangeDiv = document.createElement('div');
                    rangeDiv.className = 'range';
                    rangeDiv.style.left = `${left}px`;
                    rangeDiv.style.width = `${width}px`;

                    // Calculate size in KB
                    const sizeKB = ((data.end - data.start) / 1024).toFixed(2);

                    // Create tooltip element
                    const tooltip = document.createElement('div');
                    tooltip.className = 'tooltip';
                    tooltip.innerText = `Bytes: ${data.start}-${data.end} | Size: ${sizeKB} KB`;
                    tooltip.style.position = 'absolute';
                    tooltip.style.padding = '5px 8px';
                    tooltip.style.background = 'rgba(0,0,0,0.7)';
                    tooltip.style.color = '#fff';
                    tooltip.style.borderRadius = '4px';
                    tooltip.style.fontSize = '18px';
                    tooltip.style.pointerEvents = 'none';
                    tooltip.style.opacity = '0';
                    tooltip.style.transition = 'opacity 0.2s';
                    tooltip.style.zIndex = 10000;

                    // Show tooltip on hover
                    rangeDiv.addEventListener('mouseenter', (e) => {
                        tooltip.style.opacity = '1';
                        document.body.appendChild(tooltip);
                    });

                    rangeDiv.addEventListener('mousemove', (e) => {
                        tooltip.style.left = e.pageX + 10 + 'px';
                        tooltip.style.top = e.pageY + 10 + 'px';
                    });

                    rangeDiv.addEventListener('mouseleave', () => {
                        tooltip.style.opacity = '0';
                        tooltip.remove();
                    });

                    bar.appendChild(rangeDiv);
                }
            }
        });
    }
    // basic OSM Leaflet map
    let map = L.map('map').setView([58.15, 8], 12);
    L.tileLayer('https://cache.kartverket.no/v1/wmts/1.0.0/topograatone/default/webmercator/{z}/{y}/{x}.png', {
        maxZoom: 18,
        minZoom: 10
    }).addTo(map);

    map.getContainer().style.cursor = 'default';

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
    let rectangle = L.rectangle(getBoundForRect(), { interactive: false, color: "red", fillOpacity: 0.0, opacity: 1.0 }).addTo(map);

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
        const iter = flatgeobuf.deserialize(
            filePath,
            fgBoundingBox(), handleHeaderMeta);

        for await (const feature of iter) {
            // Leaflet styling
            const defaultStyle = {
                color: "blue",
                weight: 1,
                fillOpacity: 1,
            };
            L.geoJSON(feature, {
                style: defaultStyle,
            })
                .on({
                    'mouseover': function(e) {
                        const layer = e.target;
                        layer.setStyle({
                            weight: 4,
                            color: "green",
                            fillOpacity: 0.8,
                        });
                    },
                    'mouseout': function(e) {
                        const layer = e.target;
                        layer.setStyle(defaultStyle);
                    }
                }).bindPopup(() => {
                    const properties = feature.properties;
                    let popupContent = '<h3>Feature Info</h3><ul>';

                    for (const key in properties) {
                        if (key.includes('geometry')) {
                            // Skip geometry fields.
                            continue;
                        }
                        if (properties.hasOwnProperty(key)) {
                            popupContent += `<li><strong>${key}:</strong> ${properties[key]}</li>`;
                        }
                    }

                    popupContent += '</ul>';
                    return popupContent;
                })
                .addTo(nextResults);
        }
        rectangle.bringToFront();
    }
    // if the user is panning around alot, only update once per second max
    updateResults = _.throttle(updateResults, 1000);

    // show results based on the initial map
    updateResults();
    // ...and update the results whenever the map moves
    map.on("moveend", function(s) {
        rectangle.setBounds(getBoundForRect());
        updateResults();
        const bar = document.getElementById('fileBar');
        bar.innerHTML = '';
    });
});

