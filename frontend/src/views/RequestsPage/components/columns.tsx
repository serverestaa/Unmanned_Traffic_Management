// views/requests/column.ts
import { ColumnDef } from '@tanstack/react-table'
import { FlightRequest } from '@/api/flights'

export const requestsColumns: ColumnDef<FlightRequest>[] = [
  { accessorKey: 'id',               header: 'ID' },
  { accessorKey: 'drone_id',        header: 'Drone' },
  {
    accessorKey: 'planned_start_time',
    header: 'Start',
    cell: ({ getValue }) =>
      new Date(getValue<string>()).toLocaleString(),
  },
  {
    accessorKey: 'planned_end_time',
    header: 'End',
    cell: ({ getValue }) =>
      new Date(getValue<string>()).toLocaleString(),
  },
  { accessorKey: 'max_altitude',     header: 'Max Alt(m)' },
  { accessorKey: 'purpose',          header: 'Purpose' },
  { accessorKey: 'status',           header: 'Status' },
]
