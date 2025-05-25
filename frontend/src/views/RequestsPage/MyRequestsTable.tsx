'use client';
import { useGetMyFlightRequestsQuery } from '@/api/flights';
import { Button } from '@/components/ui/button';
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import { useRouter } from 'next/navigation';
import React from 'react'

export default function MyRequestsTable(){

    const router = useRouter();
    function startFlight(){
        router.push("/dashboard?type=in_flight");
    }
    const columns = [
        { accessorKey: 'drone_id',         header: 'Drone id' },
        { accessorKey: 'max_altitude',  header: 'Max Alt (m)' },
        { accessorKey: 'purpose',     header: 'Max Speed (m/s)' },
        { accessorKey: 'status',        header: 'Weight (kg)' },
        {
          accessorKey: 'is_active',
          header: 'Active',
          cell: ({ row }) => {
            const data  = row.original;
            if (data.status==="approved"){
                return <Button onClick={startFlight}>
                    Make flight
                </Button>
            }
            return '-'
          },
        }
    ]

    const {data=[], isLoading} = useGetMyFlightRequestsQuery();

    console.log(data);
    const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel()});
    
    return (
        <> 
        <h2>My Requests</h2>
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
        </>
    )
}