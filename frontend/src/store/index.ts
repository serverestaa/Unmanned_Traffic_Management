
import { configureStore } from '@reduxjs/toolkit';
import { userApi } from '@/api/user';
import userReducer from '@/api/user/slice';
import { droneApi } from '@/api/drone';

export const store = configureStore({
  reducer: {
    [userApi.reducerPath]: userApi.reducer,
    [droneApi.reducerPath]: droneApi.reducer,
    user: userReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(userApi.middleware, droneApi.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
