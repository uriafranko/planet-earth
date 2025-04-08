
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  variant?: 'default' | 'primary' | 'secondary' | 'accent';
  className?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  description,
  icon,
  trend,
  variant = 'default',
  className,
}) => {
  const variantClasses = {
    default: 'glass-card',
    primary: 'planet-card',
    secondary: 'bg-secondary/50 backdrop-blur-sm border border-secondary',
    accent: 'bg-gradient-to-br from-accent/20 to-accent/5 backdrop-blur-sm border border-accent/20',
  };

  const trendColors = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-muted-foreground',
  };

  return (
    <Card className={cn(variantClasses[variant], 'overflow-hidden', className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="h-5 w-5 text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center gap-2 mt-1">
          {trend && (
            <span className={cn('text-sm', trendColors[trend.direction])}>
              {trend.value > 0 && '+'}
              {trend.value}%
            </span>
          )}
          <p className="text-xs text-muted-foreground">
            {trend?.label || description}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatsCard;
