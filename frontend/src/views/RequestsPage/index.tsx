// app/requests/page.tsx
'use client'

import { useGetAllFlightRequestsQuery } from '@/api/flights'
import { RequestsDataTable } from './components/datatable'
import { requestsColumns } from './components/columns'
import { useMemo } from 'react'

export default function RequestsPage() {
    const { data = [], isLoading } = useGetAllFlightRequestsQuery();

    // stable sort by ID client-side
    const sorted = useMemo(
      () => [...data].sort((a, b) => a.id - b.id),
      [data]
    );
  

  return (
    <div className="w-full flex flex-col gap-4 p-3">
      <h1 className="text-xl font-semibold">Flight Requests</h1>
      {isLoading ? (
        <p className="text-center py-10 text-muted-foreground">Loading…</p>
      ) : (
        <RequestsDataTable data={sorted} columns={requestsColumns} />
      )}
    </div>
  )
}
