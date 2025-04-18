import React from 'react';
import { FileJson, RefreshCw, Trash } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Schema } from '@/types/models';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface SchemaCardProps {
  schema: Schema;
  onSelect: () => void;
  onDelete: () => void;
  onReindex?: () => void;
  isReindexing?: boolean;
  className?: string;
}

const SchemaCard: React.FC<SchemaCardProps> = ({
  schema,
  onSelect,
  onDelete,
  onReindex,
  isReindexing = false,
  className,
}) => {
  const timeAgo = formatDistanceToNow(new Date(schema.created_at), { addSuffix: true });

  return (
    <Card
      className={cn(
        'planet-card transition-transform hover:scale-[1.02] cursor-pointer overflow-hidden',
        className
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-0">
        <div className="h-12 w-12 rounded-full flex items-center justify-center bg-planet-primary/10 mb-3">
          <FileJson className="h-6 w-6 text-planet-primary" />
        </div>
      </CardHeader>
      <CardContent>
        <h3 className="text-lg font-semibold truncate" title={schema.title}>
          {schema.title}
        </h3>
        <div className="flex flex-col gap-1 mt-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Version</span>
            <span className="text-xs font-medium">{schema.version}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Created</span>
            <span className="text-xs">{timeAgo}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-0 flex justify-between">
        {onReindex && (
          <Button
            variant="ghost"
            size="sm"
            disabled={isReindexing}
            onClick={(e) => {
              e.stopPropagation();
              if (onReindex) onReindex();
            }}
          >
            <RefreshCw className={cn('h-4 w-4 mr-1', isReindexing && 'animate-spin')} />
            Reindex
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="hover:bg-destructive/10 hover:text-destructive"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <Trash className="h-4 w-4 mr-1" />
          Delete
        </Button>
      </CardFooter>
    </Card>
  );
};

export default SchemaCard;
