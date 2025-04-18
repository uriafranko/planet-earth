import React from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import { ScrollArea } from '@/components/ui/scroll-area';
import AppSidebar from './AppSidebar';
import Header from './Header';
import LoadingSpinner from '../LoadingSpinner';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const isLoading = false;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <ScrollArea className="flex-1">
            <main className="container mx-auto py-6">{children}</main>
          </ScrollArea>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default AppLayout;
