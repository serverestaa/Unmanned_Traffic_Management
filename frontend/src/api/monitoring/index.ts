
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { BASE_URL } from '@/lib/constants'
import { getToken } from '@/lib/tokenUtils'

/* ---------- DTOs from the OpenAPI screenshots ---------- */
export interface HexCell {
  h3_index: string
  center_lat: number
  center_lng: number
  id: number
  created_at: string
}
export interface DroneTelemetry {
  id: number
  drone_id: number
  flight_request_id: number
  hex_cell_id: number
  latitude: number
  longitude: number
  altitude: number
  speed: number
  heading: number
  battery_level: number
  status: string
  last_update: string
}
export interface ZoneDrones {
  hex_cell: HexCell
  drone_count: number
  drones: DroneTelemetry[]
}
/* ---------- API ---------- */
export const monitoringApi = createApi({
  reducerPath: 'monitoringApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${BASE_URL}/monitoring`,
    prepareHeaders: (h) => {
      const t = getToken()
      if (t) h.set('Authorization', `Bearer ${t}`)
      return h
    },
  }),
  tagTypes: ['HexCells', 'ZoneDrones'],
  endpoints: (b) => ({
    /** list of all H3 indices in DB */
    getAllHex: b.query<HexCell[], void>({
        query: () => '/all-hex',
        providesTags: ['HexCells'],
      }),
    getZoneDrones: b.query<ZoneDrones[], string[]>({
        query: (h3List) => ({
            url: '/zone/drones',
            method: 'GET',
            params: { zones: `[${h3List}]` },
        }),
        providesTags: ['ZoneDrones'],
    }),
  
  
    /** GET one cell (not used in the map below but handy) */
    getHexZone: b.query<ZoneDrones, string>({
      query: (h3) => `/zones/hex/${h3}`,
    }),
    /** other endpoints you may need later */
    getDashboard: b.query<{ active_flights:number; total_drones:number; active_alerts:number }, void>({
      query: () => '/dashboard',
    }),
  }),
})

export const {
  useGetAllHexQuery,
  useGetZoneDronesQuery,
  useGetDashboardQuery,
} = monitoringApi
