import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '@/api/user';

interface UserState {
  current: User | null;
  status: 'idle' | 'loading' | 'failed';
}
const initialState: UserState = { current: null, status: 'idle' };

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setCurrentUser: (s, a: PayloadAction<User>) => { s.current = a.payload },
    clearCurrentUser: (s) => { s.current = null },
  },
});

export const { setCurrentUser, clearCurrentUser } = userSlice.actions;
export default userSlice.reducer;
