'use client'

import { Plus } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormField,
  FormMessage,
} from '@/components/ui/form'
import { toast } from 'sonner'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  useCreateDroneMutation,
  useGetMyDronesQuery,
} from '@/api/drone'
import { DroneDataTable } from './components/DataTable'
import { droneColumns } from './components/column'
import { useState } from 'react'

/* ────────────── validation schema ────────────── */
const schema = z.object({
  brand:          z.string().nonempty('Brand is required'),
  model:          z.string().nonempty('Model is required'),
  serial_number:  z.string().nonempty('Serial number is required'),
  max_altitude:   z.number().min(1, 'Must be > 0'),
  max_speed:      z.number().min(1, 'Must be > 0'),
  weight:         z.number().min(0, 'Must be >= 0'),
})

type FormValues = z.infer<typeof schema>

export default function MyDronesPage() {
  const { data = [], isLoading } = useGetMyDronesQuery()
  const [createDrone]            = useCreateDroneMutation()
  const [open, setOpen] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      brand: '',
      model: '',
      serial_number: '',
      max_altitude: 120,
      max_speed: 15,
      weight: 0,
    },
  })

  const onSubmit = (values: FormValues) => {
    const promise = createDrone(values).unwrap()

    toast.promise(promise, {
      loading: 'Creating…',
      success: 'Drone added!',
      error:   'Failed',
    })

    promise.then(() => {
      setOpen(false)         
      form.reset()            
    })
  }


    

  return (
    <div className="w-full flex flex-col gap-4 p-3">
      {/* Header row */}
      <div className="w-full flex items-center justify-between">
        <h1 className="text-xl font-semibold">My Drones</h1>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add&nbsp;Drone
            </Button>
          </DialogTrigger>

          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add a new drone</DialogTitle>
            </DialogHeader>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                {/* Brand */}
                <FormField
                  control={form.control}
                  name="brand"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Brand</FormLabel>
                      <FormControl>
                        <Input placeholder="DJI" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Model */}
                <FormField
                  control={form.control}
                  name="model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Model</FormLabel>
                      <FormControl>
                        <Input placeholder="Mavic 3" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Serial number */}
                <FormField
                  control={form.control}
                  name="serial_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Serial #</FormLabel>
                      <FormControl>
                        <Input placeholder="SN-123456" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Max altitude */}
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

                {/* Max speed */}
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

                {/* Weight */}
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

                <Button
                  type="submit"
                  className="w-full"
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting ? 'Saving…' : 'Save'}
                </Button>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
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
