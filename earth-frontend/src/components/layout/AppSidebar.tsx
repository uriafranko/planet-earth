import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, FileJson, Home, Search, FileText } from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';
import Logo from '../Logo';

type UserRole = 'admin' | 'user' | 'viewer';

interface MenuItem {
  title: string;
  path: string;
  icon: React.ElementType;
  roles: UserRole[];
}

const AppSidebar: React.FC = () => {
  const location = useLocation();

  // Navigation menu items
  const menuItems: MenuItem[] = [
    {
      title: 'Dashboard',
      path: '/dashboard',
      icon: Home,
      roles: ['admin', 'user', 'viewer'],
    },
    {
      title: 'Schemas',
      path: '/schemas',
      icon: FileJson,
      roles: ['admin', 'user', 'viewer'],
    },
    {
      title: 'Endpoints',
      path: '/endpoints',
      icon: Database,
      roles: ['admin', 'user', 'viewer'],
    },
    {
      title: 'Documents',
      path: '/documents',
      icon: FileText,
      roles: ['admin', 'user', 'viewer'],
    },
    {
      title: 'Endpoint Search',
      path: '/search',
      icon: Search,
      roles: ['admin', 'user', 'viewer'],
    },
    {
      title: 'Document Search',
      path: '/document-search',
      icon: Search,
      roles: ['admin', 'user', 'viewer'],
    },
  ];

  return (
    <Sidebar className="border-r">
      <SidebarHeader className="flex justify-center">
        <Logo size="lg" />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.path}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.path}>
                    <Link to={item.path} className="flex items-center">
                      <item.icon className="h-5 w-5 mr-3" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};

export default AppSidebar;
