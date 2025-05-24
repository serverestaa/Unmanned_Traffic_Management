import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { BASE_URL } from '@/lib/constants';
import { getToken } from '@/lib/tokenUtils';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: 'admin' | 'pilot';
  created_at: string;
}

type SignupRequest = Omit<User, 'id' | 'created_at'> & { password: string };
type SigninRequest = { email: string; password: string };
type AuthResponse  = { access_token: string; token_type: 'bearer' };

export const userApi = createApi({
  reducerPath: 'userApi',
  tagTypes: ['User'],
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers) => {
      const token = getToken();
      if (token) headers.set('Authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  endpoints: (builder) => ({
    signin: builder.mutation<AuthResponse, SigninRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation<AuthResponse, SignupRequest>({
      query: (data) => ({
        url: '/auth/register',
        method: 'POST',
        body: data,
      }),
    }),
    getMe: builder.query<User, void>({
      query: () => ({ url: '/auth/me' }),
      providesTags: ['User'],
    }),
  }),
});

export const {
  useSigninMutation,
  useRegisterMutation,
  useLazyGetMeQuery,
  useGetMeQuery,
} = userApi;
