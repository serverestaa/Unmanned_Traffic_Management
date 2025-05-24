'use client'

import {
  Home,
  LayoutDashboard,
  Plane,
  MapIcon,
  UsersRound,
} from 'lucide-react';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { TypographyH3 } from '@/components/ui/typoh3';
import { useAppSelector } from '@/store/hooks';

const pilotItems = [
  { title: 'Home', url: '/', icon: Home },
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
  { title: 'My drones', url: '/my-drones', icon: Plane },
];

const adminItems = [
  { title: 'Online map', url: '/admin/map', icon: MapIcon },
  { title: 'All drones', url: '/admin/drones', icon: Plane },
  { title: 'Users', url: '/admin/users', icon: UsersRound },
];

export function AppSidebar() {
  const { current } = useAppSelector((s) => s.user); 
  const nav = current?.role === 'admin' ? adminItems : pilotItems;

  return (
    <Sidebar>
      <SidebarHeader>
        <TypographyH3 className="pt-1">Decedron</TypographyH3>
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
  );
}
