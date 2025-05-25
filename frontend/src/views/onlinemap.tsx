"use client";

import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Route, Trash2 } from "lucide-react";
import { useState } from "react";
import FlightModal from "./MyDronesPage/FlightModal";
import { useMapContext } from "@/context/MapContext";
import FlightModal2 from "./MyDronesPage/FlightModal2";

const MapWithDraw = dynamic(() => import("@/widgets/MapWithDraw"), {
  ssr: false,
});

export const OnlineMap = () => {
  const { mode, setMode, startPosition, endPosition, clearSelection, points } = useMapContext();
  const [flightModal, setFlightModal] = useState(false);
  const [flightModal2, setFlightModal2] = useState(false);

  function handleStartFlightProcess() {
    setFlightModal(true);
    setMode("flight_creation");
  }
  function cancelFlight() {
    setFlightModal(false);
    setMode(null);
  }

  return (
    <main className="w-full h-full p-4 flex flex-col gap-2 relative">
      <MapWithDraw />
      <aside className="absolute right-10 top-8 flex flex-col gap-4">
        <Button onClick={handleStartFlightProcess}>
          <Route size={40}/>
        </Button>
        <Button onClick={clearSelection}>
          <Trash2 size={40}/>
        </Button>
      </aside>
      {flightModal && (
        <FlightModal
          cancelFlight={cancelFlight}
          setFlightModal={setFlightModal}
          flightModal={flightModal}
        />
      )}
      {mode==="flight_creation" && (
        <>
        <aside className="absolute left-10 top-8 bg-slate-400 p-2 rounded-xl">
            <ul className="mb-2">
                {points.map((point,index)=>{
                    return <p className="p-1">{`Точка ${index}: ${point?.name}`}</p>
                })}
            </ul>
            {points.length>=2 && <Button onClick={()=>setFlightModal2(true)}>
                Сделать бронь
            </Button>}
        </aside>
        </>
      )}
      {flightModal2 && (
        <FlightModal2
          cancelFlight={cancelFlight}
          setFlightModal={setFlightModal2}
          flightModal={flightModal2}
        />
      )}
    </main>
  );
};
