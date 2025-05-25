"use client";
import { useState } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
  DialogOverlay,
  DialogPortal,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useGetMyDronesQuery } from "@/api/drone";
import { DroneDataTable } from "./components/DataTable";
import { droneColumns } from "./components/column";

import { useForm } from "react-hook-form";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";


export default function FlightModal2({
  setFlightModal: setOpen,
  flightModal: open,
  cancelFlight,
}: any) {
    const { data = [], isLoading } = useGetMyDronesQuery();
    const [selected, setSelected] = useState<string | undefined>(undefined);
    if (isLoading) {
        return <p className="text-center py-10 text-muted-foreground">Loading…</p>;
    }
    console.log(data);

    const form = useForm({
        defaultValues: {
            height: "",
            startDateTime: "",
            endDateTime: "",
        },
    });

    function onSubmit(data:any) {
        toast.promise(
            signin(data).unwrap(),
            {
              loading: 'Signing in…',
              success: () => {
                return 'Signed in!';
              },
              error: (err) => `Flight creation failed: ${err.data?.message || err.message}`,
            }
        );
    };

    return (
    <>
      {/* Dialog as Modal */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogPortal>
          <DialogContent className="fixed top-1/2 left-1/2 w-[100vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg p-6">

          <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 p-4">
                    <FormField
                    control={form.control}
                    name="height"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>Height</FormLabel>
                        <FormControl>
                            <Input {...field} placeholder="Enter height" />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                    <FormField
                    control={form.control}
                    name="startDateTime"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>Start Date & Time</FormLabel>
                        <FormControl>
                            <Input {...field} type="datetime-local" />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                    <FormField
                    control={form.control}
                    name="endDateTime"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>End Date & Time</FormLabel>
                        <FormControl>
                            <Input {...field} type="datetime-local" />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                    <Button type="submit">Submit</Button>
                </form>
                </Form>

            {/* Modal Actions */}
            <DialogFooter className="flex justify-end space-x-2">
              <DialogClose asChild>
                <Button variant="outline" onClick={cancelFlight}>Cancel</Button>
              </DialogClose>
              <Button
                onClick={() => {
                  setOpen(false);
                }}
                disabled={!selected}
              >
                Построить маршрут
              </Button>
            </DialogFooter>
          </DialogContent>
        </DialogPortal>
      </Dialog>
    </>
  );
}