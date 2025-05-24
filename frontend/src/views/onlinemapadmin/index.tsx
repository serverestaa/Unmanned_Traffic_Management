'use client';

import {
  GoogleMap,
  Circle,
  useJsApiLoader,
} from '@react-google-maps/api';
import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  useCreateRestrictedZoneMutation,
  useGetRestrictedZonesQuery,
} from '@/api/flights';
import { Label } from '@/components/ui/label';

const center = { lat: 51.1605, lng: 71.4704 };

export default function OnlineMapAdmin() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    libraries: ['drawing'],
  });

  const { data: zones = [] } = useGetRestrictedZonesQuery();
  const [createZone, { isLoading: saving }] = useCreateRestrictedZoneMutation();

  /** local UI state */
  const [draftPos, setDraftPos] = useState<google.maps.LatLngLiteral | null>(
    null
  );
  const [radius, setRadius] = useState(200); // metres

  /** click anywhere on map → show radius selector */
  const handleClick = useCallback(
    (e: google.maps.MapMouseEvent) => {
      if (!e.latLng) return;
      setDraftPos({ lat: e.latLng.lat(), lng: e.latLng.lng() });
    },
    []
  );

  /** send to backend then reset */
  const handleSave = async () => {
    if (!draftPos) return;

    await createZone({
      name: `Zone ${new Date().toLocaleTimeString()}`,
      description: '',
      center_lat: draftPos.lat,
      center_lng: draftPos.lng,
      radius,
      max_altitude: 120,
    }).unwrap();

    setDraftPos(null); // close editor
    setRadius(200);
  };

  if (loadError) return <p className="text-red-500">Map failed to load</p>;
  if (!isLoaded) return <p>Loading map…</p>;

  return (
    <main className="w-full h-full relative">
      {/* GOOGLE MAP */}
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={center}
        zoom={12}
        onClick={handleClick}
        options={{
          fullscreenControl: false,
          mapTypeControl: false,
          streetViewControl: false,
        }}
      >
        {/* existing zones */}
        {zones.map((z) => (
          <Circle
            key={z.id}
            center={{ lat: z.center_lat, lng: z.center_lng }}
            radius={z.radius}
            options={{
              fillColor: '#FF5252',
              fillOpacity: 0.25,
              strokeColor: '#FF5252',
              strokeWeight: 2,
              clickable: false,
            }}
          />
        ))}

        {/* draft preview */}
        {draftPos && (
          <Circle
            center={draftPos}
            radius={radius}
            options={{
              fillColor: '#4285F4',
              fillOpacity: 0.15,
              strokeColor: '#4285F4',
              strokeWeight: 2,
              clickable: false,
              draggable: false,
              editable: false,
            }}
          />
        )}
      </GoogleMap>

      {/* mini overlay when user clicked */}
      {draftPos && (
        <div className="absolute top-4 left-4 bg-background rounded-xl shadow-lg p-4 flex  items-center gap-2">
            <Label className="text-sm">Radius (m):</Label>
          <Input
            className="w-28"
            min={10}
            step={10}
            value={radius}
            onChange={(e) => setRadius(+e.target.value)}
            placeholder="radius m"
          />
          <Button size="sm" disabled={saving} onClick={handleSave}>
            {saving ? 'Saving…' : 'Create'}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setDraftPos(null)}
          >
            Cancel
          </Button>
        </div>
      )}
    </main>
  );
}
