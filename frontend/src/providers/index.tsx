'use client';
import { Provider } from 'react-redux';
import { ReactNode } from 'react';
import { store } from '@/store';
import { ThemeProvider } from '@/providers/theme-provider';

export function Providers({ children }: { children: ReactNode }) {
  return  <Provider store={store}>
            <ThemeProvider
              attribute="class"
              defaultTheme="dark"
              disableTransitionOnChange
            >
              {children}
            </ThemeProvider>
          </Provider>;
}
