import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { BASE_URL } from '@/lib/constants'
import { getToken } from '@/lib/tokenUtils'

/* ────────────── Types ────────────── */

export interface Drone {
  brand:          string
  model:          string
  serial_number:  string
  max_altitude:   number
  max_speed:      number
  weight:         number
  id:             string          // the backend returns number? use string to be safe
  is_active:      boolean
  owner_id:       string
  created_at:     string
}

type DronePayload = Omit<Drone, 'id' | 'owner_id' | 'created_at' | 'is_active'>

/* ────────────── API ────────────── */

export const droneApi = createApi({
  reducerPath: 'droneApi',
  tagTypes:    ['Drone'],
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (h) => {
      const token = getToken()
      if (token) h.set('Authorization', `Bearer ${token}`)
      return h
    },
  }),
  endpoints: (b) => ({
    /* GET /drones/         -> current user’s drones */
    getMyDrones: b.query<Drone[], void>({
      query: () => '/drones/',
      providesTags:  (r) => r ? [...r.map(({ id }) => ({ type: 'Drone' as const, id })), 'Drone'] : ['Drone'],
    }),

    /* GET /drones/all      -> admin only */
    getAllDrones: b.query<Drone[], void>({
      query: () => '/drones/all',
      providesTags: ['Drone'],
    }),

    /* GET /drones/{id} */
    getDrone: b.query<Drone, string>({
      query: (id) => `/drones/${id}`,
      providesTags: (_, __, id) => [{ type: 'Drone', id }],
    }),

    /* POST /drones/ */
    createDrone: b.mutation<Drone, DronePayload>({
      query: (body) => ({
        url: '/drones/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Drone'],
    }),

    /* PUT /drones/{id} */
    updateDrone: b.mutation<Drone, { id: string; data: Partial<DronePayload> }>({
      query: ({ id, data }) => ({
        url: `/drones/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Drone', id }],
    }),

    /* DELETE /drones/{id} */
    deleteDrone: b.mutation<{ ok: boolean }, string>({
      query: (id) => ({
        url: `/drones/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_, __, id) => [{ type: 'Drone', id }],
    }),
  }),
})

export const {
  useGetMyDronesQuery,
  useLazyGetDroneQuery,
  useGetAllDronesQuery,
  
  useCreateDroneMutation,
  useUpdateDroneMutation,
  useDeleteDroneMutation,
} = droneApi
