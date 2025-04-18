import React from 'react';
import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ThemeToggle from '../ThemeToggle';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';
interface HeaderProps {
  className?: string;
}

const Header: React.FC<HeaderProps> = ({ className }) => {
  return (
    <header
      className={cn(
        'w-full bg-background/80 backdrop-blur-sm z-10 border-b',
        'sticky top-0 flex items-center justify-between h-16 px-4',
        className
      )}
    >
      <div className="flex items-center gap-2">
        <SidebarTrigger>
          <Button variant="ghost" size="icon">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle sidebar</span>
          </Button>
        </SidebarTrigger>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;
