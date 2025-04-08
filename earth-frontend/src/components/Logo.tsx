
import React from 'react';
import { Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ 
  size = 'md', 
  showText = true,
  className
}) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10'
  };
  
  const textSizeClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl'
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn(
        'relative flex items-center justify-center bg-gradient-to-br from-planet-primary to-planet-secondary rounded-full p-1.5',
        'cosmic-glow'
      )}>
        <Globe className={cn('text-white', sizeClasses[size])} />
        <div className="absolute w-1.5 h-1.5 bg-planet-accent rounded-full top-1 right-1 animate-pulse-slow" />
      </div>
      
      {showText && (
        <span className={cn(
          'font-bold bg-clip-text text-transparent bg-gradient-to-r',
          'from-planet-primary to-planet-secondary',
          textSizeClasses[size]
        )}>
          Planet Earth
        </span>
      )}
    </div>
  );
};

export default Logo;
