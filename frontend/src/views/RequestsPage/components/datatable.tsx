// views/requests/RequestsDataTable.tsx
'use client'

import * as React from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  ColumnDef,
} from '@tanstack/react-table'
import {
      Dialog,
      DialogContent,
      DialogHeader,
      DialogTitle,
      DialogFooter,
      DialogTrigger,
    } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Sheet, SheetContent, SheetFooter } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import {
  FlightRequest,
  useUpdateFlightRequestStatusMutation,
} from '@/api/flights'
import RequestMapView from './RequestMapView'

// Props for the table
type Props = {
  data: FlightRequest[]
  columns: ColumnDef<FlightRequest>[]
}

export const RequestsDataTable: React.FC<Props> = ({ data, columns }) => {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })
  const [open, setOpen] = React.useState(false)
  const [rowReq, setRowReq] = React.useState<FlightRequest | null>(null)
  const [updateStatus] = useUpdateFlightRequestStatusMutation()

  const [declineOpen, setDeclineOpen] = React.useState(false)
  const [declineReason, setDeclineReason] = React.useState('')

  const [showView, setShowView] = React.useState(false);

  // when you click a row
  const handleRowClick = (r: FlightRequest) => {
    setRowReq(r)
    setOpen(true)
  }

  // Approve action
  const onApprove = async () => {
    if (!rowReq) return
    try {
      await toast.promise(
        updateStatus({
          requestId: rowReq.id,
          status: 'approved',
          approval_notes: '',
        }).unwrap(),
        { loading: 'Approving…', success: 'Approved', error: 'Failed to approve' }
      )
    } finally {
      setOpen(false)
    }
  }

  const onDeclineConfirm = async () => {
        if (!rowReq) return
        try {
          await toast.promise(
            updateStatus({
              requestId: rowReq.id,
              status: 'declined',
              approval_notes: declineReason,
            }).unwrap(),
            {
              loading: 'Declining…',
              success: 'Declined',
              error: 'Failed to decline',
            }
          )
          setDeclineOpen(false)
          setOpen(false)
        } catch {
          /* error toast already shown */
        }
      }
  
  function triggerView(){
    setShowView(true);
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
                  <th
                    key={h.id}
                    className="px-3 py-2 text-left font-semibold whitespace-nowrap"
                  >
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
                  <td
                    key={cell.id}
                    className="px-3 py-2 whitespace-nowrap"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* DETAIL SHEET */}
      <Sheet open={open} onOpenChange={(o) => setOpen(o)}>
        <SheetContent side="right" className="w-[360px] sm:w-[480px]">
          {rowReq && (
            <ScrollArea className="h-full p-4 space-y-6">
              {/* Request details */}
              <div>
                <h2 className="text-lg font-semibold mb-2">Request #{rowReq.id}</h2>
                <dl className="grid grid-cols-[140px_1fr] gap-y-1.5 text-sm">
                  <dt className="text-muted-foreground">Drone ID</dt>
                  <dd>{rowReq.drone_id}</dd>

                  <dt className="text-muted-foreground">Pilot ID</dt>
                  <dd>{rowReq.pilot_id}</dd>

                  <dt className="text-muted-foreground">Planned Start</dt>
                  <dd>
                    {new Date(rowReq.planned_start_time).toLocaleString()}
                  </dd>

                  <dt className="text-muted-foreground">Planned End</dt>
                  <dd>
                    {new Date(rowReq.planned_end_time).toLocaleString()}
                  </dd>

                  <dt className="text-muted-foreground">Max Altitude</dt>
                  <dd>{rowReq.max_altitude} m</dd>

                  <dt className="text-muted-foreground">Purpose</dt>
                  <dd>{rowReq.purpose}</dd>

                  <dt className="text-muted-foreground">Status</dt>
                  <dd>{rowReq.status}</dd>

                  {rowReq.approval_notes && (
                    <>
                      <dt className="text-muted-foreground">Notes</dt>
                      <dd>{rowReq.approval_notes}</dd>
                    </>
                  )}
                </dl>
              </div>
              <Button onClick={triggerView} className="flex-1 mt-4">
                See in map
              </Button>
              <SheetFooter className="flex gap-2 w-full mt-4">
                <Button onClick={onApprove} className="flex-1">
                  Approve
                </Button>
                <Dialog open={declineOpen} onOpenChange={setDeclineOpen}>
          <DialogTrigger asChild>
            <Button variant="destructive" className="flex-1">
              Decline
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reason for Decline</DialogTitle>
            </DialogHeader>
            <Textarea
              placeholder="Enter decline reason…"
              rows={4}
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              className="w-full"
            />
            <DialogFooter className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setDeclineOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={onDeclineConfirm}
                disabled={!declineReason.trim()}
              >
                Confirm Decline
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
              </SheetFooter>
            </ScrollArea>
          )}
        </SheetContent>
      </Sheet>
      {showView && <RequestMapView showView={showView} setShowView={setShowView} points={rowReq?.waypoints}/>}
    </>
  )
}
