import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { BASE_URL } from '@/lib/constants';  
import { getToken } from '@/lib/tokenUtils';

export interface RestrictedZone {
  id: number;
  name: string;
  description: string;
  center_lat: number;
  center_lng: number;
  radius: number;        
  max_altitude: number;
  is_active: boolean;
  created_at: string;
}
//eslint-disable-next-line @typescript-eslint/no-empty-object-type
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
//eslint-disable-next-line @typescript-eslint/no-empty-object-type
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
    getRestrictedZones: builder.query<RestrictedZone[], void>({
      query: () => '/restricted-zones',
      transformResponse: (resp: RestrictedZone[]) =>
        resp.map((z) => ({ ...z, id: Number(z.id) })),
      providesTags: (result) => [
        'RestrictedZones',
        ...(result?.map(({ id }) => ({ type: 'RestrictedZones' as const, id })) ?? [])
      ],
    }),

    createRestrictedZone: builder.mutation<RestrictedZone, NewRestrictedZone>({
      query: (body) => ({
        url: '/restricted-zones',
        method: 'POST',
        body,
      }),
      transformResponse: (z: RestrictedZone) => ({ ...z, id: Number(z.id) }),
      // Optimistic update for create
      async onQueryStarted(newZone, { dispatch, queryFulfilled }) {
        // Create temporary ID for optimistic update
        const tempId = Date.now();
        const optimisticZone = { 
          ...newZone, 
          id: tempId, 
          is_active: true, 
          created_at: new Date().toISOString() 
        };

        const patch = dispatch(
          flightsApi.util.updateQueryData(
            'getRestrictedZones',
            undefined,
            (draft) => {
              draft.push(optimisticZone);
            }
          )
        );

        try {
          const { data: createdZone } = await queryFulfilled;
          // Replace optimistic entry with real data
          dispatch(
            flightsApi.util.updateQueryData(
              'getRestrictedZones',
              undefined,
              (draft) => {
                const index = draft.findIndex(z => z.id === tempId);
                if (index !== -1) {
                  draft[index] = createdZone;
                }
              }
            )
          );
        } catch {
          patch.undo();
        }
      },
      // Only invalidate the list tag, not individual items
      invalidatesTags: ['RestrictedZones'],
    }),

    updateRestrictedZone: builder.mutation<
      RestrictedZone,
      { zoneId: number; data: Partial<NewRestrictedZone> }
    >({
      query: ({ zoneId, data }) => ({
        url: `/restricted-zones/${zoneId}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (z: RestrictedZone) => ({ ...z, id: Number(z.id) }),
      // Optimistic update for edit
      async onQueryStarted(
        { zoneId, data },
        { dispatch, queryFulfilled }
      ) {
        const patch = dispatch(
          flightsApi.util.updateQueryData(
            'getRestrictedZones',
            undefined,
            (draft) => {
              const zone = draft.find((z) => Number(z.id) === Number(zoneId));
              if (zone) {
                Object.assign(zone, data);
              }
            }
          )
        );
        
        try {
          await queryFulfilled;
        } catch {
          patch.undo();
        }
      },
      invalidatesTags: (result, error, { zoneId }) => [
        { type: 'RestrictedZones', id: zoneId }
      ],
    }),

    deleteRestrictedZone: builder.mutation<void, number>({
      query: (zoneId) => ({
        url: `/restricted-zones/${zoneId}/`,
        method: 'DELETE',
      }),
      // Optimistic update for delete
      async onQueryStarted(zoneId, { dispatch, queryFulfilled }) {
        const patch = dispatch(
          flightsApi.util.updateQueryData(
            'getRestrictedZones',
            undefined,
            (draft) => {
              const index = draft.findIndex((z) => Number(z.id) === Number(zoneId));
              if (index !== -1) {
                draft.splice(index, 1);
              }
            }
          )
        );
        
        try {
          await queryFulfilled;
        } catch {
          patch.undo();
        }
      },
      invalidatesTags: (result, error, zoneId) => [
        { type: 'RestrictedZones', id: zoneId }
      ],
    }),

    checkConflicts: builder.mutation<ConflictResponse, CheckConflictPoint[]>({
      query: (body) => ({
        url: '/check-conflicts',
        method: 'POST',
        body,
      }),
    }),

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
      providesTags: (result, error, id) => [{ type: 'FlightRequests', id }],
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
      invalidatesTags: (result, error, { requestId }) => [
        'FlightRequests',
        { type: 'FlightRequests', id: requestId },
      ],
    }),
  }),
});

export const {
  useGetRestrictedZonesQuery,
  useCreateRestrictedZoneMutation,
  useDeleteRestrictedZoneMutation,
  useCheckConflictsMutation,
  useGetMyFlightRequestsQuery,
  useGetAllFlightRequestsQuery,
  useGetFlightRequestQuery,
  useCreateFlightRequestMutation,
  useUpdateFlightRequestStatusMutation,
  useUpdateRestrictedZoneMutation
} = flightsApi;