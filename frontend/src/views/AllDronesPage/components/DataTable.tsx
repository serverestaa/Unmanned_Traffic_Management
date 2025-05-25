'use client'

import * as React from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  ColumnDef,
} from '@tanstack/react-table'
import {
  Sheet,
  SheetContent,
} from '@/components/ui/sheet'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Drone,
} from '@/api/drone'

type Props = {
  data: Drone[]
  columns: ColumnDef<Drone, unknown>[]
}

export const DroneDataTable: React.FC<Props> = ({ data, columns }) => {
  const [open, setOpen]         = React.useState(false)
  const [rowDrone, setRowDrone] = React.useState<Drone | null>(null)


  /* react-table setup */
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })

  const handleRowClick = (d: Drone) => {
    setRowDrone(d)
    setOpen(true)
  }



  return (
    <>
      {/* TABLE */}
      <div className="rounded-md border w-full overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b bg-muted/50">
                {hg.headers.map((h) => (
                  <th key={h.id} className="px-3 py-2 text-left font-semibold whitespace-nowrap">
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b hover:bg-muted cursor-pointer"
                onClick={() => handleRowClick(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SHEET */}
      <Sheet open={open} onOpenChange={(o) => { setOpen(o); }}>
        <SheetContent side="right" className="w-[360px] sm:w-[480px]">

          {/* DISPLAY mode */}
          {rowDrone && (
            <ScrollArea className="h-full p-4 space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-2">Drone details</h2>
                <dl className="grid grid-cols-[140px_1fr] gap-y-1.5 text-sm">
                  {Object.entries(rowDrone).map(([k, v]) => (
                    <React.Fragment key={k}>
                      <dt className="text-muted-foreground capitalize">{k.replace(/_/g, ' ')}</dt>
                      <dd className="truncate">{String(v)}</dd>
                    </React.Fragment>
                  ))}
                </dl>
              </div>
            </ScrollArea>
          )}
        </SheetContent>
      </Sheet>
    </>
  )
}
