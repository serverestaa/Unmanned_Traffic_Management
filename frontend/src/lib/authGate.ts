'use client';

import { useEffect } from 'react';
import { useAppDispatch } from '@/store/hooks';
import { useLazyGetMeQuery } from '@/api/user';
import { getToken } from '@/lib/tokenUtils';
import { clearCurrentUser, setCurrentUser } from '@/api/user/slice';

export const AuthGate = () => {
  const dispatch = useAppDispatch();
  const [getMe]   = useLazyGetMeQuery();

  useEffect(() => {
    if (!getToken()) return;        
    getMe()
      .unwrap()
      .then((u) => dispatch(setCurrentUser(u)))
      .catch(() => {
        dispatch(clearCurrentUser());
      });
  }, [dispatch, getMe]);

  return null; 
};
