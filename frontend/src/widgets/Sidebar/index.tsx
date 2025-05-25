'use client'

import {
  Home,
  LayoutDashboard,
  Plane,
  HexagonIcon,
  UsersRound,
  Laptop
} from 'lucide-react'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { TypographyH3 } from '@/components/ui/typoh3'
import { useAppSelector } from '@/store/hooks'

const guestItems = [
  { title: 'Home', url: '/', icon: Home },
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
]

const pilotItems = [
  { title: 'Home', url: '/', icon: Home },
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
  { title: 'My drones', url: '/my-drones', icon: Plane },
]

const adminItems = [
  { title: 'Restricted zones', url: '/admin/map', icon: HexagonIcon },
  { title: 'Monitoring', url: '/admin/monitoring', icon: Laptop },
  { title: 'All drones', url: '/admin/drones', icon: Plane },
  { title: 'Requests', url: '/admin/requests', icon: UsersRound }
]

export function AppSidebar() {
  const { current } = useAppSelector((s) => s.user)

  const nav = !current
    ? guestItems
    : current.role === 'admin'
    ? adminItems
    : pilotItems

  return (
    <Sidebar>
      <SidebarHeader>
        <TypographyH3 className="pt-1">Decedrone</TypographyH3>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {nav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
