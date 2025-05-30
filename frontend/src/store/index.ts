
import { configureStore } from '@reduxjs/toolkit';
import { userApi } from '@/api/user';
import userReducer from '@/api/user/slice';
import { droneApi } from '@/api/drone';
import restrictedZonesReducer from '@/api/flights/slice'
import { flightsApi } from '@/api/flights';
import { monitoringApi } from '@/api/monitoring';

export const store = configureStore({
  reducer: {
    [userApi.reducerPath]: userApi.reducer,
    [droneApi.reducerPath]: droneApi.reducer,
    user: userReducer,
    restrictedZones: restrictedZonesReducer, 
    [flightsApi.reducerPath]: flightsApi.reducer,
    [monitoringApi.reducerPath]: monitoringApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(userApi.middleware, droneApi.middleware, flightsApi.middleware, monitoringApi.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
