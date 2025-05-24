import { ColumnDef } from '@tanstack/react-table'
import { Drone } from '@/api/drone'

export const droneColumns: ColumnDef<Drone>[] = [
  { accessorKey: 'brand',         header: 'Brand' },
  { accessorKey: 'model',         header: 'Model' },
  { accessorKey: 'serial_number', header: 'Serial #' },
  { accessorKey: 'max_altitude',  header: 'Max Alt (m)' },
  { accessorKey: 'max_speed',     header: 'Max Speed (m/s)' },
  { accessorKey: 'weight',        header: 'Weight (kg)' },
  {
    accessorKey: 'is_active',
    header: 'Active',
    cell: ({ getValue }) => (getValue<boolean>() ? '✓' : '—'),
  },
]
