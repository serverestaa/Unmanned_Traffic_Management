"use client";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
  DialogPortal,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useGetMyDronesQuery } from "@/api/drone";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useMapContext } from "@/context/MapContext";

export default function FlightModal({
  setFlightModal: setOpen,
  flightModal: open,
  cancelFlight,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
}: any) {
    const { data = [], isLoading } = useGetMyDronesQuery();
    const [selected, setSelected] = useState<string | undefined>(undefined);
    const {
      setCurrentDrone
  } = useMapContext();
    if (isLoading) {
        return <p className="text-center py-10 text-muted-foreground">Loading…</p>;
    }
    return (
    <>
      {/* Dialog as Modal */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogPortal>
          <DialogContent className="fixed top-1/2 left-1/2 w-[100vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg p-6">
            <DialogHeader>
              <DialogTitle>Confirm Action</DialogTitle>
            </DialogHeader>
            <Select value={selected} onValueChange={setSelected}>
                <SelectTrigger>
                    <SelectValue placeholder="Select device..." />
                </SelectTrigger>
                <SelectContent>
                    {data.map((drone, idx) => (
                        <SelectItem
                        key={idx}
                        value={`${drone.brand}|${drone.model}|${drone.serial_number}`}
                        onClick={setCurrentDrone(drone)}>
                        <div className="grid grid-cols-3 gap-4">
                            <span>{drone.brand}</span>
                            <span>{drone.model}</span>
                            <span>{drone.serial_number}</span>
                        </div>
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
            {selected && (
                <div className="mt-2 text-sm text-gray-600">
                Selected: {selected.split("|").join(" — ")}
                </div>
            )}

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
