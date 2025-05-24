// api/flights/index.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { BASE_URL } from '@/lib/constants';   // already used elsewhere
import { getToken } from '@/lib/tokenUtils';

/* ---------- Types ---------- */

export interface RestrictedZone {
  id: number;
  name: string;
  description: string;
  center_lat: number;
  center_lng: number;
  radius: number;          // metres
  max_altitude: number;
  is_active: boolean;
  created_at: string;
}

export interface NewRestrictedZone
  extends Omit<RestrictedZone, 'id' | 'is_active' | 'created_at'> {}

export interface Waypoint {
  latitude: number;
  longitude: number;
  altitude: number;
  sequence: number;
}

export interface FlightRequest {
  id: number;
  drone_id: number;
  pilot_id: string;
  planned_start_time: string;
  planned_end_time: string;
  max_altitude: number;
  purpose: string;
  status: string;
  approval_notes: string | null;
  approved_by: string | null;
  created_at: string;
  approved_at: string | null;
  waypoints: Waypoint[];
  drone?: Record<string, unknown>;
  pilot?: Record<string, unknown>;
}

export interface NewFlightRequest
  extends Omit<
    FlightRequest,
    | 'id'
    | 'pilot_id'
    | 'status'
    | 'approval_notes'
    | 'approved_by'
    | 'created_at'
    | 'approved_at'
    | 'drone'
    | 'pilot'
  > {}

export interface CheckConflictPoint {
  latitude: number;
  longitude: number;
  altitude: number;
}

export interface ConflictResponse {
  has_conflicts: boolean;
  conflicts: Waypoint[];
  restricted_zones: RestrictedZone[];
}

/* ---------- API ---------- */

export const flightsApi = createApi({
  reducerPath: 'flightsApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${BASE_URL}/flights`,
    prepareHeaders: (h) => {
          const token = getToken()
          if (token) h.set('Authorization', `Bearer ${token}`)
          return h
        },
  }),
  tagTypes: ['RestrictedZones', 'FlightRequests'],
  endpoints: (builder) => ({
    /* ----- restricted zones ----- */
    getRestrictedZones: builder.query<RestrictedZone[], void>({
      query: () => '/restricted-zones',
      providesTags: ['RestrictedZones'],
    }),
    createRestrictedZone: builder.mutation<RestrictedZone, NewRestrictedZone>({
      query: (body) => ({
        url: '/restricted-zones',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['RestrictedZones'],
    }),
    deleteRestrictedZone: builder.mutation<string, number>({
      query: (zoneId) => ({
        url: `/restricted-zones/${zoneId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['RestrictedZones'],
    }),

    /* ----- conflict check ----- */
    checkConflicts: builder.mutation<ConflictResponse, CheckConflictPoint[]>({
      query: (body) => ({
        url: '/check-conflicts',
        method: 'POST',
        body,
      }),
    }),

    /* ----- flight requests (CRUD) ----- */
    getMyFlightRequests: builder.query<FlightRequest[], void>({
      query: () => '/requests',
      providesTags: ['FlightRequests'],
    }),
    getAllFlightRequests: builder.query<FlightRequest[], void>({
      query: () => '/requests/all',
      providesTags: ['FlightRequests'],
    }),
    getFlightRequest: builder.query<FlightRequest, number>({
      query: (id) => `/requests/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'FlightRequests', id }],
    }),
    createFlightRequest: builder.mutation<FlightRequest, NewFlightRequest>({
      query: (body) => ({
        url: '/requests',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['FlightRequests'],
    }),
    updateFlightRequestStatus: builder.mutation<
      FlightRequest,
      { requestId: number; status: string; approval_notes?: string }
    >({
      query: ({ requestId, ...body }) => ({
        url: `/requests/${requestId}`,
        method: 'PUT',
        body,
      }),
      invalidatesTags: (_r, _e, { requestId }) => [
        'FlightRequests',
        { type: 'FlightRequests', id: requestId },
      ],
    }),
  }),
});

export const {
  /* hooks we’ll need in UI */
  useGetRestrictedZonesQuery,
  useCreateRestrictedZoneMutation,
  useDeleteRestrictedZoneMutation,
  useCheckConflictsMutation,
  useGetMyFlightRequestsQuery,
  useGetAllFlightRequestsQuery,
  useGetFlightRequestQuery,
  useCreateFlightRequestMutation,
  useUpdateFlightRequestStatusMutation,
} = flightsApi;
