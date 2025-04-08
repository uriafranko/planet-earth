
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface MethodBadgeProps {
  method: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const MethodBadge: React.FC<MethodBadgeProps> = ({ 
  method, 
  size = 'md',
  className
}) => {
  const methodConfig: Record<string, { bg: string; text: string }> = {
    GET: { bg: 'bg-blue-500/20 border-blue-500/30', text: 'text-blue-700 dark:text-blue-300' },
    POST: { bg: 'bg-green-500/20 border-green-500/30', text: 'text-green-700 dark:text-green-300' },
    PUT: { bg: 'bg-amber-500/20 border-amber-500/30', text: 'text-amber-700 dark:text-amber-300' },
    PATCH: { bg: 'bg-purple-500/20 border-purple-500/30', text: 'text-purple-700 dark:text-purple-300' },
    DELETE: { bg: 'bg-red-500/20 border-red-500/30', text: 'text-red-700 dark:text-red-300' },
  };

  const config = methodConfig[method.toUpperCase()] || { 
    bg: 'bg-gray-500/20 border-gray-500/30', 
    text: 'text-gray-700 dark:text-gray-300' 
  };

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-0.5',
    lg: 'px-2.5 py-1'
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        config.bg,
        config.text,
        'font-mono font-bold',
        sizeClasses[size],
        className
      )}
    >
      {method.toUpperCase()}
    </Badge>
  );
};

export default MethodBadge;
