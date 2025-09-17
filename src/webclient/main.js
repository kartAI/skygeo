import './style.css';
import { Map, View } from 'ol';
import TileLayer from 'ol/layer/WebGLTile';
// import OSM from 'ol/source/OSM';
import GeoTIFF from 'ol/source/GeoTIFF';
import ImageTile from 'ol/source/ImageTile';

const cog = new GeoTIFF({
  normalize: false,
  sources: [
    { url: 'https://karttest.nibio.no/skygeo/sr16/bonitet_3857_cog.tif' }
  ]
});

const bonitet = ['band', 1];

const map = new Map({
  target: 'map',
  layers: [
    // new TileLayer({ source: new OSM() }),
    new TileLayer({
      source: new ImageTile({
        url: 'https://cache.kartverket.no/v1/wmts/1.0.0/topograatone/default/webmercator/{z}/{y}/{x}.png'
      })
    }),
    new TileLayer({
      source: cog,
      style: { color:
        [
          'case',
          ['==', bonitet, -9999], 'transparent',
          ['==', bonitet, 0], 'transparent',
          ['<', bonitet, 7], [247, 252, 245],
          ['<', bonitet, 9], [229, 245, 224],
          ['<', bonitet, 13], [199, 233, 192],
          ['<', bonitet, 16], [161, 217, 155],
          ['<', bonitet, 19], [116, 196, 118],
          ['<', bonitet, 22], [65, 171, 93],
          ['<', bonitet, 25], [35, 139, 69],
          ['<', bonitet, 29], [0, 90, 50],
          'darkgreen'
        ]
      }
    })
  ],
  // view: cog.getView()
  view: new View({ center: [1100000, 9300000], zoom: 6 })
});

// map.on('click', event => console.log(map.getLayers().item(1).getData(event.pixel)));
