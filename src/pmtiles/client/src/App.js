import { useEffect } from "react";
import "./styles.css";
import Map from "react-map-gl";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";

export default function App() {
  useEffect(() => {
    let protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    return () => {
      maplibregl.removeProtocol("pmtiles");
    };
  }, []);

  return (
    <div className="App">
      <h1>Cloud Native Demo</h1>
      <Map
        initialViewState={{
          longitude: 8.0182,
          latitude: 58.1599,
          zoom: 11
        }}
        style={{ width: 800, height: 600 }}
        cursor="default"
        mapStyle={{
          version: 8,
          sources: {
            N50_Vei: {
              type: "vector",
              url: "pmtiles://http://localhost:8000/N50_Samferdsel_senterlinje.pmtiles"
            },
            N50_Bygg: {

              type: "vector",
              url: "pmtiles://http://localhost:8000/N50_BygningerOgAnlegg_omrade.pmtiles"
            },
            N50_Raster: {
              type: "raster",
              url: "pmtiles://http://localhost:8000/N50_raster_2024.pmtiles"
            }
          },
          layers: [
            {
              id: "raster",
              source: "N50_Raster",
              type: "raster"
            },
            {
              id: "veier",
              source: "N50_Vei",
              "source-layer": "N50_Samferdsel_senterlinje",
              type: "line",
              paint: {
                "line-color": "#999"
              }
            },
            {
              id: "bygninger",
              source: "N50_Bygg",
              "source-layer": "N50_BygningerOgAnlegg_omrade",
              type: "fill",
              paint: {
                "fill-color": "#fcba03"
              }
            }
          ]
        }}
        mapLib={maplibregl}
      />
      <div>Eksempelet viser tre datalag som hentes fra .pmtiles filer</div>
      <div>Alle data er hentet fra det åpne datasettet N50.</div>
      <div style={{color:"#999"}}>Samferdsel senterlinje</div>
      <div style={{color:"#fcba03"}}>Bygninger og anlegg område</div>
      <div>Raster kartdata</div>
    </div>
  );
}
