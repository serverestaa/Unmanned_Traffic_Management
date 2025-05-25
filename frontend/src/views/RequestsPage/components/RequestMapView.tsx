"use client"
import React from 'react'
import {
  GoogleMap,
  Circle,                        
  useJsApiLoader,
  Polyline,
} from '@react-google-maps/api';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogPortal,
} from "@/components/ui/dialog";
import { useGetRestrictedZonesQuery } from '@/api/flights';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const RequestMapView = ({points, showView, setShowView}:any) => {


    const { isLoaded } = useJsApiLoader({
        googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
        libraries: ['drawing'],
    });

    const { data: zones = [] } = useGetRestrictedZonesQuery();

    const middleLatitude = points.reduce((acc: any,cur: { latitude: any; })=>{return acc+cur.latitude}, 0)/points.length;
    const middleLongitude = points.reduce((acc: any,cur: { longitude: any; })=>{return acc+cur.longitude}, 0)/points.length;

    const center = {lat: middleLatitude, lng:middleLongitude};
    console.log(points);
    return (
        <Dialog open={showView} onOpenChange={setShowView}>
        <DialogPortal>
        <DialogContent className="sm:max-w-3xl w-full p-0">
            <DialogHeader>
            <DialogTitle>Map Interaction</DialogTitle>
            <DialogDescription>
                Click on the circle to see a message.
            </DialogDescription>
            </DialogHeader>
            {!isLoaded ? (
            <div className="p-4">Loading map…</div>
            ) : (
            <GoogleMap
                mapContainerStyle={{ width: "100%", height: "400px" }}
                center={center}
                zoom={12}
            >
                {zones.map((z) => (
                    <Circle
                    key={z.id}
                    center={{ lat: z.center_lat, lng: z.center_lng }}
                    radius={z.radius}                 
                    options={{
                        clickable: false,
                        fillColor: '#FF5252',
                        fillOpacity: 0.25,
                        strokeColor: '#FF5252',
                        strokeWeight: 2,
                    }}
                    />
                ))}
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {points.length>=2 && points.map((_: any,index: number)=>{
                    if (index==points.length-1) return;
                    
                    return (
                        <Polyline
                        key={index}
                            path={[
                            {lat: points[index].lat || points[index].latitude, 
                                lng: points[index].lng || points[index].longitude},
                            {lat: points[index+1].lat || points[index+1].latitude, 
                                lng: points[index+1].lng || points[index+1].longitude}
                            ]}
                            options={{
                            strokeOpacity: 0.8,
                            strokeWeight: 4,
                            }}
                        />
                    );
                })}
            </GoogleMap>
            )}
        </DialogContent>
        </DialogPortal>
      </Dialog>
    )
}

export default RequestMapView