'use client';
import {
  GoogleMap,
  DrawingManager,
  Polygon,
  useJsApiLoader,
} from '@react-google-maps/api';
import { useCallback, useRef, useState } from 'react';

const center = { lat: 51.1605, lng: 71.4704 };

export default function MapWithDraw() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    libraries: ['drawing'],
  });

  const [polys, setPolys] = useState<{ id: string; path: google.maps.LatLngLiteral[] }[]>([]);
  const nextId = useRef(0);

  const handlePolygonComplete = useCallback((p: google.maps.Polygon) => {
    const path = p.getPath().getArray().map((pt) => ({
      lat: pt.lat(),
      lng: pt.lng(),
    }));
    setPolys((old) => [...old, { id: `poly-${nextId.current++}`, path }]);
    p.setMap(null);
  }, []);

  if (loadError) return <p className="text-red-500">Map failed to load</p>;
  if (!isLoaded)   return <p>Loading map…</p>;

  return (
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '100%' }}
      center={center}
      zoom={12}
      options={{
        fullscreenControl: false,
        mapTypeControl: false,
        streetViewControl: false,
      }}
    >
      {polys.map((poly) => (
        <Polygon
          key={poly.id}
          paths={poly.path}
          options={{
            fillColor: '#4285F4',
            fillOpacity: 0.3,
            strokeColor: '#4285F4',
            strokeWeight: 2,
            editable: true,
          }}
        />
      ))}

      <DrawingManager
        onPolygonComplete={handlePolygonComplete}
        options={{
          drawingControl: true,
          drawingControlOptions: {
            drawingModes: [google.maps.drawing.OverlayType.POLYGON],
            position: google.maps.ControlPosition.TOP_CENTER,
          },
          polygonOptions: {
            fillColor: '#4285F4',
            fillOpacity: 0.3,
            strokeColor: '#4285F4',
            strokeWeight: 2,
          },
        }}
      />
    </GoogleMap>
  );
}
