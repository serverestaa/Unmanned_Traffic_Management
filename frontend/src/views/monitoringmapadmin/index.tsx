'use client'

import { useState, useMemo } from 'react'
import { useJsApiLoader, GoogleMap, Polygon, OverlayView } from '@react-google-maps/api'
import { cellToBoundary } from 'h3-js'
import {
  useGetAllHexQuery,
  useGetZoneDronesQuery,
} from '@/api/monitoring'
import { PlaneIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
    HoverCard,
    HoverCardTrigger,
    HoverCardContent,
  } from '@/components/ui/hover-card'
const center = { lat: 51.1605, lng: 71.4704 }

export default function MonitoringMapAdmin() {
  const { data: cells = [], isLoading: loadingHex } = useGetAllHexQuery()
  
  const [selected, setSelected] = useState<string[]>([])
  
  const {
    data: zones = [],
  } = useGetZoneDronesQuery(selected, {
    skip: selected.length === 0,
  })
  
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
  })

  const polys = useMemo(() =>
    cells.map((cell) => {
      const h3   = cell.h3_index
      const path = cellToBoundary(h3)          // no `true` ⇒ returns [lat, lng]
        .map(([lat, lng]) => ({ lat, lng }))
  
      return { h3, path }
    })
  , [cells])

  const toggle = (h3: string) =>
    setSelected((prev) =>
      prev.includes(h3) ? prev.filter((x) => x !== h3) : [...prev, h3]
    )

  const drones = zones.flatMap((z) => z.drones)

  if (loadError)   return <p className="text-red-500">Map failed to load</p>
  if (!isLoaded)   return <p>Loading map…</p>

  return (
    <div className="w-full h-full relative">
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={center}
        zoom={11}
        options={{
          mapTypeControl:   false,
          streetViewControl:false,
        }}
      >
        {polys.map(({ h3, path }) => (
          <Polygon
            key={h3}
            paths={path}
            onClick={() => toggle(h3)}
            options={{
              strokeWeight:  1,
              strokeOpacity: 0.8,
              // default blue stroke
              strokeColor:   selected.includes(h3) ? '#1e3a8a' : '#2563eb',
              // default blue fill
              fillOpacity:   0.25,
              fillColor:     selected.includes(h3) ? '#1e40af' : '#3b82f6',
            }}
          />
        ))}

        {drones.map((d) => (
          <OverlayView
            key={d.id}
            position={{ lat: d.latitude, lng: d.longitude }}
            mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
          >
            <HoverCard>
              <HoverCardTrigger asChild>
                <Button
                  size="icon"
                  variant={selected.includes(d.hex_cell_id.toString()) ? 'default' : 'outline'}
                  className="!p-1 !text-xs !rounded-full !bg-white !shadow-md"
                >
                  <PlaneIcon className="h-4 w-4" />
                </Button>
              </HoverCardTrigger>
              <HoverCardContent side="top" className="w-40">
                <p className="font-semibold">Drone #{d.drone_id}</p>
                <p>Battery: {d.battery_level}%</p>
                <p>Altitude: {d.altitude} m</p>
              </HoverCardContent>
            </HoverCard>
          </OverlayView>
        ))}
      </GoogleMap>

      <div className="absolute top-4 left-4 flex gap-2">
        <span className="text-xs pt-2 text-muted-foreground">
          {loadingHex ? 'loading hex…' : `${cells.length} cells`}
        </span>
      </div>
    </div>
  )
}
