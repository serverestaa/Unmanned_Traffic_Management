"use client";
import React, { createContext, useContext, useState, ReactNode } from 'react';

/**
 * Geographic coordinates
 */
export interface LatLng {
  lat: number;
  lng: number;
}

/**
 * A drone flight consisting of a start and end position
 */
export interface Flight {
  id: string;
  start: LatLng;
  end: LatLng;
}

/**
 * Context state and actions for map interactions and drone flights
 */
interface MapContextType {
  /** All created flights */
  flights: Flight[];
  /** Currently selected start position */
  startPosition: LatLng | null;
  /** Currently selected end position */
  endPosition: LatLng | null;
  /** Set the start position for a new flight */
  setStartPosition: (pos: LatLng) => void;
  /** Set the end position for a new flight */
  setEndPosition: (pos: LatLng) => void;
  /** Create a flight from the selected start and end */
  createFlight: () => void;
  /** Reset the current start/end selection */
  clearSelection: () => void;
  mode: any,
  setMode: any,
  addPosition: any,
  points: any,
  currentDrone: any,
  setCurrentDrone: any
}

const MapContext = createContext<MapContextType | undefined>(undefined);

export const MapProvider = ({ children }: { children: ReactNode }) => {
    const [flights, setFlights] = useState<Flight[]>([]);
    const [startPosition, setStart] = useState<LatLng | null>(null);
    const [endPosition, setEnd] = useState<LatLng | null>(null);
    
    const [points, setPoints] = useState<LatLng[]>([]);
    const [mode, setMode] = useState<any>(null);

    const [currentDrone, setCurrentDrone] = useState();

    const setStartPosition = (pos: LatLng) => {
        setStart(pos);
        setPoints([pos]);
    };

    const addPosition = (pos: LatLng) => {
        setPoints(prev=>[...prev, pos]);
        setEndPosition(pos);
    };

    const setEndPosition = (pos: LatLng) => {
        setEnd(pos);
    };

    const createFlight = async () => {

    };

    const clearSelection = () => {
        setStart(null);
        setEnd(null);
        setMode(null);
        setPoints([]);
        setCurrentDrone(undefined);
    };

    console.log(mode, startPosition, endPosition);
    return (
        <MapContext.Provider
        value={{
            flights,
            startPosition,
            endPosition,
            setStartPosition,
            setEndPosition,
            createFlight,
            clearSelection,
            mode,
            setMode,
            addPosition,
            points,
            currentDrone,
            setCurrentDrone
        }}
        >
        {children}
        </MapContext.Provider>
    );
};

/**
 * Custom hook to access map context
 */
export function useMapContext(): MapContextType {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error('useMapContext must be used within a MapProvider');
  }
  return context;
}
