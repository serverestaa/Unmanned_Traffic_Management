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
  SheetFooter,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import {
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormField,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import {
  Drone,
  useDeleteDroneMutation,
  useUpdateDroneMutation,
} from '@/api/drone'
import { useForm } from 'react-hook-form'

/* -------------------------------- Helpers ------------------------------- */

const editSchema = z.object({
  brand:         z.string().nonempty(),
  model:         z.string().nonempty(),
  serial_number: z.string().nonempty(),
  max_altitude:  z.number().min(1),
  max_speed:     z.number().min(1),
  weight:        z.number().min(0),
  is_active:     z.boolean(),
})
type EditValues = z.infer<typeof editSchema>

type Props = {
  data: Drone[]
  columns: ColumnDef<Drone, unknown>[]
}

export const DroneDataTable: React.FC<Props> = ({ data, columns }) => {
  const [open, setOpen]         = React.useState(false)
  const [editing, setEditing]   = React.useState(false)
  const [rowDrone, setRowDrone] = React.useState<Drone | null>(null)

  /* mutations */
  const [updateDrone] = useUpdateDroneMutation()
  const [deleteDrone] = useDeleteDroneMutation()

  /* react-table setup */
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })

  const startEdit = () => setEditing(true)
  const stopEdit  = () => setEditing(false)

  const handleRowClick = (d: Drone) => {
    setRowDrone(d)
    setOpen(true)
  }

  /* --------------------------- Edit form setup --------------------------- */
  const form = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    values: rowDrone
      ? {
          brand:         rowDrone.brand,
          model:         rowDrone.model,
          serial_number: rowDrone.serial_number,
          max_altitude:  rowDrone.max_altitude,
          max_speed:     rowDrone.max_speed,
          weight:        rowDrone.weight,
          is_active:     rowDrone.is_active,
        }
      : undefined,
  })

  const onSave = form.handleSubmit(async (values) => {
    if (!rowDrone) return
    await toast.promise(
      updateDrone({ id: rowDrone.id, data: values }).unwrap(),
      { loading: 'Updating…', success: 'Saved', error: 'Failed' },
    )
    stopEdit()
  })

  const onDelete = async () => {
    if (!rowDrone) return
    if (!confirm('Delete this drone?')) return
    await toast.promise(
      deleteDrone(rowDrone.id).unwrap(),
      { loading: 'Deleting…', success: 'Deleted', error: 'Failed' },
    )
    setOpen(false)
  }

  /* ---------------------------------------------------------------------- */

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
      <Sheet open={open} onOpenChange={(o) => { setOpen(o); stopEdit() }}>
        <SheetContent side="right" className="w-[360px] sm:w-[480px]">

          {/* DISPLAY mode */}
          {rowDrone && !editing && (
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

              <SheetFooter className="flex gap-2 w-full mt-4">
                <Button className='w-full' onClick={startEdit}>Edit</Button>
                <Button className='w-full' variant="destructive" onClick={onDelete}>
                  Delete
                </Button>
              </SheetFooter>
            </ScrollArea>
          )}

          {/* EDIT mode */}
          {rowDrone && editing && (
            <ScrollArea className="h-full p-4">
              <h2 className="text-lg font-semibold mb-4">Update drone</h2>

              <Form {...form}>
                <form onSubmit={onSave} className="space-y-4">
                  {/** brand */}
                  <FormField
                    control={form.control}
                    name="brand"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Brand</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** model */}
                  <FormField
                    control={form.control}
                    name="model"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Model</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** serial # */}
                  <FormField
                    control={form.control}
                    name="serial_number"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Serial #</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** max altitude */}
                  <FormField
                    control={form.control}
                    name="max_altitude"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max altitude (m)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(+e.target.value)}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** max speed */}
                  <FormField
                    control={form.control}
                    name="max_speed"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max speed (m/s)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(+e.target.value)}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** weight */}
                  <FormField
                    control={form.control}
                    name="weight"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Weight (kg)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(+e.target.value)}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/** active switch */}
                  <FormField
                    control={form.control}
                    name="is_active"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-lg border p-3">
                        <FormLabel className="m-0">Active</FormLabel>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      className="flex-1"
                      onClick={stopEdit}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      className="flex-1"
                      disabled={form.formState.isSubmitting}
                    >
                      {form.formState.isSubmitting ? 'Saving…' : 'Save'}
                    </Button>
                  </div>
                </form>
              </Form>
            </ScrollArea>
          )}
        </SheetContent>
      </Sheet>
    </>
  )
}
