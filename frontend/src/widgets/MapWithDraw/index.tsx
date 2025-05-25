'use client';
import {
  GoogleMap,
  DrawingManager,
  Polygon,
  Circle,                        
  useJsApiLoader,
  Polyline,
  InfoWindow
} from '@react-google-maps/api';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  useGetRestrictedZonesQuery,     
} from '@/api/flights';

const center = { lat: 51.1605, lng: 71.4704 };
import { useMapContext } from '@/context/MapContext';


export default function MapWithDraw() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    libraries: ['drawing'],
  });

  const [info, setInfo] = useState<{
    position: google.maps.LatLngLiteral;
    text: string;
  } | null>(null);
  console.log(info)

  const onCircleClick = (evt: google.maps.MapMouseEvent) => {
    if (!evt.latLng) return;
    setInfo({
      position: { lat: evt.latLng.lat(), lng: evt.latLng.lng() },
      text: "Красная зона!",
    });
  };

  const { data: zones = [] } = useGetRestrictedZonesQuery();
  const {mode,
    startPosition,
    setStartPosition,
    addPosition,
    points,
  } = useMapContext();

  const handleClick = async (e: google.maps.MapMouseEvent) => {
    if (!e.latLng) return;
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    const res = await fetch(
      `https://maps.googleapis.com/maps/api/geocode/json?` +
        new URLSearchParams({
          latlng: `${lat},${lng}`,
          key: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
        })
    );
    const json = await res.json();

    const first = json.results?.[0];
    const name = first?.formatted_address || "Unknown location";
    const components = first?.address_components || [];
    const loc = {
      name, components,lat,lng
    }
    if (mode==="flight_creation"){
      if (!startPosition) {
        // 1st click: set start
        setStartPosition(loc);
      } else{
        addPosition(loc);
      }
    }
  };



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



  useEffect(()=>{
    async function fetchDrones(){

    }
  },[]);



  if (loadError) return <p className="text-red-500">Map failed to load</p>;
  if (!isLoaded) return <p>Loading map…</p>;


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
      onClick={handleClick}
    >
      {zones.map((z) => (
        <Circle
          key={z.id}
          center={{ lat: z.center_lat, lng: z.center_lng }}
          radius={z.radius}                 
          options={{
            clickable: true,
            fillColor: '#FF5252',
            fillOpacity: 0.25,
            strokeColor: '#FF5252',
            strokeWeight: 2,
          }}
          onClick={onCircleClick}
        />
      ))}
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {points.length>=2 && points.map((_: any,index: number)=>{
        if (index==points.length-1) return;
        
        return (
          <Polyline
            path={[
              {lat: points[index].lat, lng: points[index].lng},
              {lat: points[index+1].lat, lng: points[index+1].lng}
            ]}
            key={index}
            options={{
              strokeOpacity: 0.8,
              strokeWeight: 4,
            }}
          />
        );
      })}
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
      {info && (
        <InfoWindow
          position={info.position}
          onCloseClick={() => setInfo(null)}
        >
          <div className='text-red-800 font-bold text-lg'>{info.text}</div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
}
