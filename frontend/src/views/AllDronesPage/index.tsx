'use client'

import {
  useGetAllDronesQuery,
} from '@/api/drone'
import { DroneDataTable } from './components/DataTable'
import { droneColumns } from './components/column'

export default function MyDronesPage() {
  const { data = [], isLoading } = useGetAllDronesQuery()

  return (
    <div className="w-full flex flex-col gap-4 p-3">
      {/* Header row */}
      <div className="w-full flex items-center justify-between">
        <h1 className="text-xl font-semibold">All Drones</h1>
      </div>

      {/* Data table */}
      {isLoading ? (
        <p className="text-center py-10 text-muted-foreground">Loading…</p>
      ) : (
        <DroneDataTable data={data} columns={droneColumns} />
      )}
    </div>
  )
}
