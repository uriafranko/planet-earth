import React from 'react';
import { FileText, Trash } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Document } from '@/types/models';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface DocumentCardProps {
  document: Document;
  onSelect: () => void;
  onDelete: () => void;
  className?: string;
}

const DocumentCard: React.FC<DocumentCardProps> = ({ document, onSelect, onDelete, className }) => {
  const timeAgo = formatDistanceToNow(new Date(document.created_at || new Date()), {
    addSuffix: true,
  });

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
          <FileText className="h-6 w-6 text-planet-primary" />
        </div>
      </CardHeader>
      <CardContent>
        <h3 className="text-lg font-semibold truncate" title={document.title}>
          {document.title}
        </h3>
        <div className="flex flex-col gap-1 mt-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Type</span>
            <span className="text-xs font-medium">{document.file_type}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Created</span>
            <span className="text-xs">{timeAgo}</span>
          </div>
          {document.original_filename && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-muted-foreground">Original</span>
              <span className="text-xs">{document.original_filename}</span>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="pt-0 flex justify-end">
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

export default DocumentCard;
