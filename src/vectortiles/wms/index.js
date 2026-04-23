import path from 'path';

import { viewport } from '@mapbox/geo-viewport';
import mbgl from '@maplibre/maplibre-gl-native';
import express from 'express';
import proj4 from 'proj4';
import sharp from 'sharp';

const transformer = proj4('EPSG:4326', 'EPSG:3857');
const fromLonLat = (x, y) => transformer.forward([x, y]);
const toLonLat = (x, y) => transformer.inverse([x, y]);

const response = await fetch('https://demotiles.maplibre.org/style.json');
const styles = await response.json();

const app = express();

const map = new mbgl.Map();
map.load(styles);

app.get('/', (req, res) => {
    const file = path.join(process.cwd(), 'index.html');
    res.sendFile(file);
});

app.get('/favicon.ico', (req, res) => {
    const file = path.join(process.cwd(), 'favicon.ico');
    res.sendFile(file);
});

app.get('/ows', (req, res) => {
    const {
        BBOX = '',
        CRS = '',
        FORMAT = '',
        HEIGHT = '',
        REQUEST = '',
        SERVICE = '',
        VERSION = '',
        WIDTH = '',
    } = req.query;

    if (SERVICE.toLowerCase() !== 'wms') return res.status(400).send('SERVICE');
    if (VERSION.startsWith('1.') === false) return res.status(400).send('VERSION');
    if (REQUEST.toLowerCase() !== 'getmap') return res.status(400).send('REQUEST');
    if (FORMAT !== 'image/png' && FORMAT !== 'image/jpeg') return res.status(400).send('FORMAT');
    if (CRS.toLowerCase() !== 'epsg:3857') return res.status(400).send('EPSG');
    if (BBOX === '') return res.status(400).send('BBOX');
    if (HEIGHT === '') return res.status(400).send('HEIGHT');
    if (WIDTH === '') return res.status(400).send('WIDTH');

    const format = FORMAT.split('/').pop();
    const bbox = BBOX.split(',').map(parseFloat);
    const height = parseInt(HEIGHT);
    const width = parseInt(WIDTH);

    const bounds = [...toLonLat(bbox[0], bbox[1]), ...toLonLat(bbox[2], bbox[3])];
    const { center, zoom } = viewport(bounds, [width, height], 0, 22, 512, true, true);
    
    map.render({ center, height, width, zoom }, function(err, buffer) {
        if (err) {
            return res.status(500).send({ err });
        }

        const image = sharp(buffer, {
            raw: {
                channels: 4,
                height,
                width,
            },
        }).toFormat(format).toBuffer().then(data => {
            return res.type(format).send(data);
        });
    });
});

app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000')
});
