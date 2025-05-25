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
import { useCreateFlightRequestMutation } from "@/api/flights";
import { useMapContext } from "@/context/MapContext";
import { TypographyP } from "@/components/ui/typop";


export default function FlightModal2({
  setFlightModal: setOpen,
  flightModal: open,
  cancelFlight,
}: any) {

    const {currentDrone, points} = useMapContext();

    const form = useForm({
        defaultValues: {
            height: "",
            startDateTime: "",
            endDateTime: "",
        },
    });

    function onSubmit(formData:any) {
        toast.promise(
            useCreateFlightRequestMutation(formData),
            {
              loading: 'Flight creation...',
              success: ({data}) => {
                return 'Flight created!!';
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
                    <TypographyP>
                        {`Drone: ${currentDrone}`}
                    </TypographyP>
                    <TypographyP>
                        Points
                    </TypographyP>
                    <ul>
                        {points.map((point,index)=>{
                            return (
                                <TypographyP>
                                    {`Point ${index+1}: ${point.name}`}
                                </TypographyP>
                            )
                        })}
                    </ul>
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