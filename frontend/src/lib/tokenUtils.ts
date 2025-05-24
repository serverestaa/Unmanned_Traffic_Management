
const TOKEN_KEY = 'access_token';

export const saveToken = (token: string) =>
  typeof window !== 'undefined' && localStorage.setItem(TOKEN_KEY, token);

export const getToken = () =>
  (typeof window !== 'undefined' && localStorage.getItem(TOKEN_KEY)) || null;

export const clearToken = () =>
  typeof window !== 'undefined' && localStorage.removeItem(TOKEN_KEY);
