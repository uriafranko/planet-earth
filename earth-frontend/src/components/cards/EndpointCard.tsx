
import React from 'react';
import { Endpoint } from '@/types/models';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import MethodBadge from '../MethodBadge';

interface EndpointCardProps {
  endpoint: Endpoint;
  onViewDetails: () => void;
  className?: string;
}

const EndpointCard: React.FC<EndpointCardProps> = ({ 
  endpoint, 
  onViewDetails,
  className
}) => {
  // Extract tags array from string
  const tags = endpoint.tags ? endpoint.tags.split(',').map(t => t.trim()) : [];
  
  return (
    <Card className={cn('glass-card overflow-hidden h-full flex flex-col', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <MethodBadge method={endpoint.method} />
          {endpoint.deleted_at && (
            <Badge variant="destructive">Deleted</Badge>
          )}
        </div>
        <h3 className="font-mono text-sm mt-2" title={endpoint.path}>
          {endpoint.path}
        </h3>
        {endpoint.operation_id && (
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold">Operation:</span> {endpoint.operation_id}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex-1">
        {endpoint.summary && (
          <p className="text-sm mb-2 line-clamp-2" title={endpoint.summary}>
            {endpoint.summary}
          </p>
        )}
        
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {tags.map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-0">
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full"
          onClick={onViewDetails}
        >
          <Info className="h-4 w-4 mr-1" />
          Details
        </Button>
      </CardFooter>
    </Card>
  );
};

export default EndpointCard;
