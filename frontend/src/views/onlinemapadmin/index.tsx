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
  useDeleteRestrictedZoneMutation,
  useGetRestrictedZonesQuery,
  RestrictedZone,
  useUpdateRestrictedZoneMutation,
} from '@/api/flights';
import { Label } from '@/components/ui/label';

const center = { lat: 51.1605, lng: 71.4704 };

export default function OnlineMapAdmin() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
    libraries: ['drawing'],
  });

  /* data & mutations */
  const {
    data: zones = [],
    refetch,                     
  } = useGetRestrictedZonesQuery();
  const [createZone]  = useCreateRestrictedZoneMutation();
  const [deleteZone]  = useDeleteRestrictedZoneMutation();
  const [updateZone]  = useUpdateRestrictedZoneMutation();

  /* ui state */
  const [draftPos, setDraftPos]               = useState<google.maps.LatLngLiteral | null>(null);
  const [draftRadius, setDraftRadius]         = useState(200);

  const [selected, setSelected]               = useState<RestrictedZone | null>(null);
  const [selectedRadius, setSelectedRadius]   = useState<number>(0);

  /* ---------- create ---------- */
  const handleMapClick = useCallback((e: google.maps.MapMouseEvent) => {
    if (!e.latLng) return;
    setDraftPos({ lat: e.latLng.lat(), lng: e.latLng.lng() });
  }, []);

  const handleSaveDraft = async () => {
    if (!draftPos) return;
    await createZone({
      name: `Zone ${new Date().toLocaleTimeString()}`,
      description: '',
      center_lat: draftPos.lat,
      center_lng: draftPos.lng,
      radius: draftRadius,
      max_altitude: 120,
    }).unwrap();
    setDraftPos(null);
    setDraftRadius(200);
  };

  /* ---------- edit / delete ---------- */
  const handleCircleClick = (z: RestrictedZone) => {
    setSelected(z);
    setSelectedRadius(z.radius);
    setDraftPos(null);           // hide any in-progress draft
  };

  const handleUpdate = async () => {
    if (!selected) return;
    await updateZone({ zoneId: selected.id, data: { radius: selectedRadius } }).unwrap();
    setSelected(null);
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      await deleteZone(selected.id).unwrap();
    } finally {
      refetch();                   //  <── guarantee the list is fresh
      setSelected(null);
    }
  };
  

  /* ---------- render ---------- */
  if (loadError) return <p className="text-red-500">Map failed to load</p>;
  if (!isLoaded)   return <p>Loading map…</p>;

  return (
    <main className="w-full h-full relative">
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={center}
        zoom={12}
        onClick={handleMapClick}
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
            onClick={() => handleCircleClick(z)}
            options={{
              fillColor: selected?.id === z.id ? '#2962FF' : '#FF5252',
              fillOpacity: 0.25,
              strokeColor: selected?.id === z.id ? '#2962FF' : '#FF5252',
              strokeWeight: 2,
            }}
          />
        ))}

        {/* draft preview */}
        {draftPos && (
          <Circle
            center={draftPos}
            radius={draftRadius}
            options={{
              fillColor: '#4285F4',
              fillOpacity: 0.15,
              strokeColor: '#4285F4',
              strokeWeight: 2,
            }}
          />
        )}
      </GoogleMap>

      {/* overlay for NEW zone */}
      {draftPos && (
        <div className="absolute top-4 left-4 bg-background rounded-xl shadow-lg p-4 flex items-end gap-2">
          <Input
            type="number"
            className="w-28"
            min={10}
            step={10}
            value={draftRadius}
            onChange={(e) => setDraftRadius(+e.target.value)}
            placeholder="radius m"
          />
          <Button size="sm" onClick={handleSaveDraft}>Create</Button>
          <Button size="sm" variant="ghost" onClick={() => setDraftPos(null)}>
            Cancel
          </Button>
        </div>
      )}

      {/* overlay for EDIT / DELETE */}
      {selected && (
        <div className="absolute top-4 left-4 bg-background rounded-xl shadow-lg p-4 flex items-center gap-2">
            <Label className="mr-2">Radius (m):</Label>
          <Input
            className="w-28"
            min={10}
            step={10}
            value={selectedRadius}
            onChange={(e) => setSelectedRadius(+e.target.value)}
          />
          <Button size="sm" onClick={handleUpdate}>Save</Button>
          <Button size="sm" variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelected(null)}>
            Close
          </Button>
        </div>
      )}
    </main>
  );
}
