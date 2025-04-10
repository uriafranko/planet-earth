import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, FileJson, Home, LogOut, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import { useAuth } from '@/contexts/AuthContext';
import UserAvatar from '../UserAvatar';
import RoleIndicator from '../RoleIndicator';

type UserRole = 'admin' | 'user' | 'viewer';

interface MenuItem {
  title: string;
  path: string;
  icon: React.ElementType;
  roles: UserRole[];
}

const AppSidebar: React.FC = () => {
  const { user, logout, hasRole } = useAuth();
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
      title: 'Search',
      path: '/search',
      icon: Search,
      roles: ['admin', 'user', 'viewer'],
    },
  ];

  // Filter menu items based on user role
  const filteredMenuItems = menuItems.filter((item) => hasRole(item.roles));

  return (
    <Sidebar className="border-r">
      <SidebarHeader className="flex justify-center py-6">
        <Logo size="lg" />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {filteredMenuItems.map((item) => (
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

      {user && (
        <SidebarFooter className="border-t p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <UserAvatar user={user} size="sm" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user.name}</span>
                <RoleIndicator role={user.role} size="sm" />
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </SidebarFooter>
      )}
    </Sidebar>
  );
};

export default AppSidebar;
