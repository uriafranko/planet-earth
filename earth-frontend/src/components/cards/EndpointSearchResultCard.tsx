import React from 'react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { EndpointSearchResult } from '@/types/models';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import MethodBadge from '../MethodBadge';

interface EndpointSearchResultCardProps {
  result: EndpointSearchResult;
  onSelect: () => void;
  className?: string;
}

const EndpointSearchResultCard: React.FC<EndpointSearchResultCardProps> = ({ result, onSelect, className }) => {
  // Format score as percentage
  const scorePercentage = Math.round(result.score * 100);

  // Determine the color based on score
  const getScoreColor = () => {
    if (scorePercentage >= 90) return 'text-green-600 dark:text-green-400';
    if (scorePercentage >= 70) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <Card className={cn('glass-card h-full flex flex-col', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <MethodBadge method={result.method} />
          <div className={cn('text-sm font-medium', getScoreColor())}>{scorePercentage}% match</div>
        </div>
        <h3 className="font-mono text-sm mt-2" title={result.path}>
          {result.path}
        </h3>
      </CardHeader>
      <CardContent className="flex-1">
        {result.summary && <p className="text-sm mb-2">{result.summary}</p>}

        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">API</span>
            <span className="font-medium">{result.schema_title}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Version</span>
            <span>{result.schema_version}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-0">
        <Button variant="default" size="sm" className="w-full" onClick={onSelect}>
          <ExternalLink className="h-4 w-4 mr-2" />
          View Endpoint
        </Button>
      </CardFooter>
    </Card>
  );
};
export default EndpointSearchResultCard;
