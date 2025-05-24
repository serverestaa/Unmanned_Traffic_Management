'use client'

import dynamic from 'next/dynamic';

const MapWithDraw = dynamic(() => import('@/widgets/MapWithDraw'), {
    ssr: false,
  });

export const OnlineMap = () => {
    return (
        <main className="w-full h-full p-4 flex flex-col gap-2">
            <MapWithDraw />
        </main>
    )
} 