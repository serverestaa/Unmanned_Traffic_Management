'use client';

import {
  GoogleMap,
  Circle,
  useJsApiLoader,
} from '@react-google-maps/api';
import { useState, useCallback, useEffect } from 'react';
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
  });

  /* data & mutations */
  const {
    data: zones = [],
    isLoading,
    error,
  } = useGetRestrictedZonesQuery(undefined, {
    // Reduce refetch frequency to prevent constant data updates
    refetchOnMountOrArgChange: true,
    refetchOnFocus: false,
    refetchOnReconnect: true,
  });
  
  const [createZone, { isLoading: isCreating }] = useCreateRestrictedZoneMutation();
  const [deleteZone, { isLoading: isDeleting }] = useDeleteRestrictedZoneMutation();
  const [updateZone, { isLoading: isUpdating }] = useUpdateRestrictedZoneMutation();

  /* ui state */
  const [draftPos, setDraftPos] = useState<google.maps.LatLngLiteral | null>(null);
  const [draftRadius, setDraftRadius] = useState(200);

  const [selected, setSelected] = useState<RestrictedZone | null>(null);
  const [selectedRadius, setSelectedRadius] = useState<number>(0);

  // Reset selected zone if it no longer exists in zones array
  useEffect(() => {
    if (selected && !zones.find(z => z.id === selected.id)) {
      setSelected(null);
    }
  }, [zones, selected]);

  /* ---------- create ---------- */
  const handleMapClick = useCallback((e: google.maps.MapMouseEvent) => {
    if (!e.latLng) return;
    setDraftPos({ lat: e.latLng.lat(), lng: e.latLng.lng() });
    // Clear selection when creating new zone
    setSelected(null);
  }, []);

  const handleSaveDraft = async () => {
    if (!draftPos || isCreating) return;
    
    try {
      await createZone({
        name: `Zone ${new Date().toLocaleTimeString()}`,
        description: '',
        center_lat: draftPos.lat,
        center_lng: draftPos.lng,
        radius: draftRadius,
        max_altitude: 120,
      }).unwrap();
      
      // Clear draft state after successful creation
      setDraftPos(null);
      setDraftRadius(200);
    } catch (error) {
      console.error('Failed to create zone:', error);
    }
  };

  /* ---------- edit / delete ---------- */
  const handleCircleClick = (z: RestrictedZone) => {
    setSelected(z);
    setSelectedRadius(z.radius);
    setDraftPos(null); // hide any in-progress draft
  };

  const handleUpdate = async () => {
    if (!selected || isUpdating) return;
    
    try {
      await updateZone({ 
        zoneId: selected.id, 
        data: { radius: selectedRadius } 
      }).unwrap();
      
      // Don't clear selection immediately - let the optimistic update handle it
      // The useEffect above will clear it if needed
    } catch (error) {
      console.error('Failed to update zone:', error);
    }
  };
  
  const handleDelete = async () => {
    if (!selected || isDeleting) return;
    
    try {
      await deleteZone(selected.id).unwrap();
      // Clear selection immediately since zone will be removed
      setSelected(null);
    } catch (error) {
      console.error('Failed to delete zone:', error);
    }
  };

  /* ---------- render ---------- */
  if (loadError) return <p className="text-red-500">Map failed to load: {loadError.message}</p>;
  if (!isLoaded) return <p>Loading map…</p>;
  if (error) return <p className="text-red-500">Failed to load zones</p>;

  return (
    <main className="w-full h-full relative">
      {isLoading && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 bg-white p-4 rounded shadow">
          Loading zones...
        </div>
      )}
      
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
            key={`zone-${z.id}`} // More explicit key
            center={{ lat: z.center_lat, lng: z.center_lng }}
            radius={z.radius}
            onClick={() => handleCircleClick(z)}
            options={{
              fillColor: selected?.id === z.id ? '#2962FF' : '#FF5252',
              fillOpacity: 0.25,
              strokeColor: selected?.id === z.id ? '#2962FF' : '#FF5252',
              strokeWeight: 2,
              clickable: true,
            }}
          />
        ))}

        {/* draft preview */}
        {draftPos && (
          <Circle
            key="draft-circle"
            center={draftPos}
            radius={draftRadius}
            options={{
              fillColor: '#4285F4',
              fillOpacity: 0.15,
              strokeColor: '#4285F4',
              strokeWeight: 2,
              clickable: false,
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
            disabled={isCreating}
          />
          <Button 
            size="sm" 
            onClick={handleSaveDraft}
            disabled={isCreating}
          >
            {isCreating ? 'Creating...' : 'Create'}
          </Button>
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={() => setDraftPos(null)}
            disabled={isCreating}
          >
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
            type="number"
            min={10}
            step={10}
            value={selectedRadius}
            onChange={(e) => setSelectedRadius(+e.target.value)}
            disabled={isUpdating || isDeleting}
          />
          <Button 
            size="sm" 
            onClick={handleUpdate}
            disabled={isUpdating || isDeleting}
          >
            {isUpdating ? 'Saving...' : 'Save'}
          </Button>
          <Button 
            size="sm" 
            variant="destructive" 
            onClick={handleDelete}
            disabled={isUpdating || isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={() => setSelected(null)}
            disabled={isUpdating || isDeleting}
          >
            Close
          </Button>
        </div>
      )}
    </main>
  );
}