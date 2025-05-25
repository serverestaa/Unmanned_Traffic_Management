'use client'

import { useState, useMemo } from 'react'
import { useJsApiLoader, GoogleMap, Polygon, Marker } from '@react-google-maps/api'
import { cellToBoundary } from 'h3-js'
import {
  useGetAllHexQuery,
  useGetZoneDronesQuery,
} from '@/api/monitoring'

// map center
const center = { lat: 51.1605, lng: 71.4704 }

function planeSvg(col = '#dc2626'): google.maps.Symbol {
  return {
    path:        'M1 10 L21 12 L21 8 L1 6 L0 7 L0 11 Z',
    fillColor:   col,
    fillOpacity: 1,
    scale:       1,
    strokeWeight:0,
  }
}

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
          <Marker
            key={d.id}
            position={{ lat: d.latitude, lng: d.longitude }}
            icon={planeSvg()}
            title={`Drone ${d.drone_id}\nAlt ${d.altitude} m\nBatt ${d.battery_level}%`}
          />
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
