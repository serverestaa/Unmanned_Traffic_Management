
import {
    createEntityAdapter,
    createSlice,
  } from '@reduxjs/toolkit';
  import { RestrictedZone } from '@/api/flights';
  import { flightsApi } from '@/api/flights';
  
  const adapter = createEntityAdapter<RestrictedZone>({
      sortComparer: (a, b) => a.name.localeCompare(b.name),
    });
  
  const slice = createSlice({
    name: 'restrictedZones',
    initialState: adapter.getInitialState(),
    reducers: {
    },
    extraReducers: (builder) => {
      builder.addMatcher(
        flightsApi.endpoints.getRestrictedZones.matchFulfilled,
        (state, { payload }) => {
          adapter.setAll(state, payload);
        }
      );
      builder.addMatcher(
        flightsApi.endpoints.createRestrictedZone.matchFulfilled,
        (state, { payload }) => {
          adapter.addOne(state, payload);
        }
      );
      builder.addMatcher(
        flightsApi.endpoints.updateRestrictedZone.matchFulfilled,
        (state, { payload }) => {
          adapter.upsertOne(state, payload);        // <- update radius etc.
        }
      );
      
      builder.addMatcher(
        flightsApi.endpoints.deleteRestrictedZone.matchFulfilled,
        (state, { meta }) => {
          adapter.removeOne(state, Number(meta.arg.originalArgs)); // id is numeric
        }
      );
      
    },
  });
  
  export const restrictedZonesSelectors = adapter.getSelectors<{
    restrictedZones: ReturnType<typeof slice.reducer>;
  }>((s) => s.restrictedZones);
  
  export default slice.reducer;
  