import { useEffect, useRef } from 'react';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import GeoJSON from 'ol/format/GeoJSON';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import { Stroke, Style, Circle, Fill } from 'ol/style';
import { fromLonLat } from 'ol/proj';
import 'ol/ol.css';

const STAGE_COLORS = {
  first_mile: '#2ecc71',
  linehaul: '#e74c3c',
  last_mile: '#3498db',
};

function routeStyle(feature) {
  const stage = feature.get('stage');
  return new Style({
    stroke: new Stroke({
      color: STAGE_COLORS[stage] || '#999999',
      width: stage === 'linehaul' ? 4 : 2,
    }),
  });
}

function vehicleStyle(feature) {
  const stage = feature.get('stage');
  return new Style({
    image: new Circle({
      radius: 7,
      fill: new Fill({ color: STAGE_COLORS[stage] || '#000000' }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
    }),
  });
}

export default function MapView() {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const vehicleSourceRef = useRef(null);
  const vehicleFeaturesRef = useRef({}); // key -> Feature, để cập nhật vị trí thay vì tạo mới mỗi lần
  const wsRef = useRef(null);

  useEffect(() => {
  let map;

  if (!mapInstance.current) {
    const vectorSource = new VectorSource();
    const vehicleSource = new VectorSource();
    vehicleSourceRef.current = vehicleSource;

    map = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        new VectorLayer({ source: vectorSource, style: routeStyle }),
        new VectorLayer({ source: vehicleSource, style: vehicleStyle }),
      ],
      view: new View({ center: fromLonLat([106.4, 20.9]), zoom: 9 }),
    });
    mapInstance.current = map;

    fetch('http://localhost:8000/routes/latest')
      .then((res) => res.json())
      .then((geojson) => {
        const features = new GeoJSON().readFeatures(geojson, {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:3857',
        });
        vectorSource.addFeatures(features);
        if (features.length > 0) {
          map.getView().fit(vectorSource.getExtent(), { padding: [40, 40, 40, 40] });
        }
      })
      .catch((err) => console.error('Lỗi tải routes:', err));
  } else {
    map = mapInstance.current;
    map.setTarget(mapRef.current);
  }

  // --- Phần WebSocket giờ nằm NGOÀI nhánh if/else, luôn chạy mỗi lần effect thực thi ---
  const ws = new WebSocket('ws://localhost:8000/ws/vehicles');
  wsRef.current = ws;

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (!data.vehicles) return;

    data.vehicles.forEach((v) => {
      if (!v.position) return;
      const coord = fromLonLat(v.position);
      let feature = vehicleFeaturesRef.current[v.key];
      if (!feature) {
        feature = new Feature({ geometry: new Point(coord) });
        feature.set('stage', v.stage);
        feature.set('hub_zone', v.hub_zone);
        vehicleFeaturesRef.current[v.key] = feature;
        vehicleSourceRef.current.addFeature(feature);
      } else {
        feature.getGeometry().setCoordinates(coord);
      }
    });
  };

  ws.onerror = (err) => console.error('Lỗi WebSocket:', err);

  return () => {
    map.setTarget(null);
    ws.close();
  };
}, []);

  return <div ref={mapRef} style={{ width: '100%', height: '600px' }} />;
}