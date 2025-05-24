'use client'

import { Fragment } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ModeToggle } from '@/components/mode-toggle'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { useAppSelector } from '@/store/hooks'

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

const LABELS: Record<string, string> = {
  '':        'Decedron',
  dashboard: 'Dashboard',
  drones:    'My drones',
  signin:    'Sign in',
  signup:    'Sign up',
  profile:   'Profile',
}

const humanize = (slug: string) =>
  LABELS[slug] ??
  slug.replace(/[-_]/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())

const buildHref = (segments: string[], idx: number) =>
  '/' + segments.slice(0, idx + 1).filter(Boolean).join('/')

/* ------------------------------------------------------------------ */
/* Component                                                          */
/* ------------------------------------------------------------------ */

export const Header = () => {
  const pathname    = usePathname()
  const { current } = useAppSelector((s) => s.user)

  // "/" → [""]   |  "/drones/42" → ["", "drones", "42"]
  const segments =
    pathname === '/' ? [''] : ['', ...pathname.split('/').filter(Boolean)]

  return (
    <div className="w-full flex items-center justify-between border-b p-2">
      <div className="flex items-center gap-2">
        <SidebarTrigger />

        <Breadcrumb>
          <BreadcrumbList>
            {segments.map((seg, i) => {
              const href   = buildHref(segments, i)
              const isLast = i === segments.length - 1
              const label  =
                seg && /^[0-9a-fA-F-]{6,}$/.test(seg)
                  ? `Drone ${seg.slice(0, 6)}…`
                  : humanize(seg)

              return (
                <Fragment key={href}>
                  <BreadcrumbItem className="capitalize">
                    {isLast ? (
                      <span aria-current="page" className="text-muted-foreground">
                        {label}
                      </span>
                    ) : (
                      <BreadcrumbLink asChild>
                        <Link href={href}>{label}</Link>
                      </BreadcrumbLink>
                    )}
                  </BreadcrumbItem>

                  {/* separator must be a sibling of the item, NOT its child */}
                  {!isLast && <BreadcrumbSeparator />}
                </Fragment>
              )
            })}
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className="flex items-center gap-2">
        <ModeToggle />
        {current ? (
          <Button asChild variant="outline">
            <Link href="/profile">Profile</Link>
          </Button>
        ) : (
          <Button asChild variant="outline">
            <Link href="/signin">Sign in</Link>
          </Button>
        )}
      </div>
    </div>
  )
}
