import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Drone } from '@/api/drone'

interface DroneState {
  selected: Drone | null
}
const initialState: DroneState = { selected: null }

const droneSlice = createSlice({
  name: 'drone',
  initialState,
  reducers: {
    setSelectedDrone: (s, a: PayloadAction<Drone | null>) => { s.selected = a.payload },
  },
})

export const { setSelectedDrone } = droneSlice.actions
export default droneSlice.reducer
