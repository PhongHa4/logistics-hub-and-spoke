import { useEffect, useRef } from 'react';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import GeoJSON from 'ol/format/GeoJSON';
import { Stroke, Style } from 'ol/style';
import 'ol/ol.css';
import { fromLonLat } from 'ol/proj';

// Màu khác nhau theo từng giai đoạn, để phân biệt trên map
const STAGE_COLORS = {
  first_mile: '#2ecc71',   // xanh lá
  linehaul: '#e74c3c',     // đỏ
  last_mile: '#3498db',    // xanh dương
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

export default function MapView() {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);

  useEffect(() => {
  if (mapInstance.current) {
    // Nếu map đã tồn tại (do StrictMode chạy lại), chỉ cần gắn lại vào div
    mapInstance.current.setTarget(mapRef.current);
    return () => mapInstance.current.setTarget(null);
  }

  const vectorSource = new VectorSource();

  const map = new Map({
    target: mapRef.current,
    layers: [
      new TileLayer({ source: new OSM() }),
      new VectorLayer({ source: vectorSource, style: routeStyle }),
    ],
    view: new View({
      center: fromLonLat([106.4, 20.9]),
      zoom: 9,
    }),
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

  return () => {
    map.setTarget(null);
  };
}, []);

  return <div ref={mapRef} style={{ width: '100%', height: '600px' }} />;
}