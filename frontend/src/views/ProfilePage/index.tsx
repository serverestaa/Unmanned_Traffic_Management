// app/profile/page.tsx
'use client'

import { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { clearToken } from '@/lib/tokenUtils'
import { clearCurrentUser, setCurrentUser } from '@/api/user/slice'
import { TypographyP } from '@/components/ui/typop'

export default function ProfilePage() {
  const dispatch = useAppDispatch()
  const router = useRouter()
  const {current: user} = useAppSelector((s) => s.user)

  // sync into Redux state
  useEffect(() => {
    if (user) {
      dispatch(setCurrentUser(user))
    }
  }, [user, dispatch])

  const handleLogout = () => {
    clearToken()
    dispatch(clearCurrentUser())
    router.push('/signin')
  }

  if (!user)     return <TypographyP className="p-4 text-center">No user data found.</TypographyP>
  return (
    <div className="w-full mx-auto p-6 space-y-4">
      <div className="space-y-2">
        <TypographyP><strong>Full Name:</strong> {user.full_name}</TypographyP>
        <TypographyP><strong>Email:</strong>     {user.email}</TypographyP>
        <TypographyP><strong>Phone:</strong>     {user.phone}</TypographyP>
        <TypographyP><strong>Role:</strong>      {user.role}</TypographyP>
        <TypographyP>
          <strong>Member since:</strong>{' '}
          {new Date(user.created_at).toLocaleDateString()}
        </TypographyP>
      </div>
      <Button variant="destructive" onClick={handleLogout}>
        Logout
      </Button>
    </div>
  )
}
