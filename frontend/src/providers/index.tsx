'use client';
import { Provider } from 'react-redux';
import { ReactNode } from 'react';
import { store } from '@/store';
import { ThemeProvider } from '@/providers/theme-provider';
import { SidebarProvider } from "@/components/ui/sidebar"
import { Toaster } from 'sonner';
import { AuthGate } from '@/lib/authGate';

export function Providers({ children }: { children: ReactNode }) {
  return  <Provider store={store}>
            <ThemeProvider
              attribute="class"
              defaultTheme="dark"
              disableTransitionOnChange
            >
              <SidebarProvider>
                <Toaster position="top-right" />
                <AuthGate />
                {children}
              </SidebarProvider>
            </ThemeProvider>
          </Provider>;
}
