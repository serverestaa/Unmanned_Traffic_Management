
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { User } from '@/api/user';

interface UserState {
  current: User | null;
  all: User[];
  status: 'idle' | 'loading' | 'failed';
}

const initialState: UserState = {
  current: null,
  all: [],
  status: 'idle',
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setCurrentUser(state, action: PayloadAction<User>) {
      state.current = action.payload;
    },
    clearCurrentUser(state) {
      state.current = null;
    },
    setAllUsers(state, action: PayloadAction<User[]>) {
      state.all = action.payload;
    },
    clearAllUsers(state) {
      state.all = [];
    },
    setStatus(state, action: PayloadAction<UserState['status']>) {
      state.status = action.payload;
    },
  },
});

export const {
  setCurrentUser,
  clearCurrentUser,
  setAllUsers,
  clearAllUsers,
  setStatus,
} = userSlice.actions;

export default userSlice.reducer;
