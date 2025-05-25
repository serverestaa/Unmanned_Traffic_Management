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

    const {currentDrone, points, clearSelection} = useMapContext();
    const [createRequest] = useCreateFlightRequestMutation();

    const form = useForm({
        defaultValues: {
            max_altitude: "",
            planned_start_time: "",
            planned_end_time: "",
            purpose: ""
        },
    });
    console.log(currentDrone);

    function onSubmit(formData:any) {
        formData.drone_id = currentDrone.id;
        formData.pilot_id = currentDrone.owner_id;
        formData.waypoints = points.map((point,index)=>{
            return {latitude:point.lat, longitude:point.lng, sequence: index+1, altitude: formData.max_altitude}
        });
        console.log(formData);

        const promise = createRequest(formData).unwrap();
        toast.promise(
            promise,
            {
              loading: 'Request sending...',
              success: (data) => {
                console.log(data);
                return 'Request sent!';
              },
              error: (err) => {
                console.log(err);
                return `Request creation failed: ${err.data?.message || err.message}`
              },
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
                        {`Drone id: ${currentDrone.id}`}
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
                        name="purpose"
                        render={({ field }) => (
                            <FormItem>
                            <FormLabel>Purpose</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder="Purpose" />
                            </FormControl>
                            <FormMessage />
                            </FormItem>
                        )}
                    />
                    <FormField
                        control={form.control}
                        name="max_altitude"
                        render={({ field }) => (
                            <FormItem>
                            <FormLabel>Max Height</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder="Enter max height" />
                            </FormControl>
                            <FormMessage />
                            </FormItem>
                        )}
                    />
                    <FormField
                        control={form.control}
                        name="planned_start_time"
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
                        name="planned_end_time"
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
                    <Button type="submit">Отправить запрос</Button>
                </form>
                </Form>

          </DialogContent>
        </DialogPortal>
      </Dialog>
    </>
  );
}