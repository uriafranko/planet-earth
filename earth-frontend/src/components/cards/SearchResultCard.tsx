import React from 'react';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import ReactMarkdown from 'react-markdown';
import type { DocumentSearchResult } from '@/types/models';

interface SearchResultCardProps {
  result: DocumentSearchResult;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({ result }) => {
  const [open, setOpen] = React.useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <div
          className="border rounded-md p-4 bg-background cursor-pointer hover:shadow transition"
          tabIndex={0}
          role="button"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') setOpen(true);
          }}
        >
          <div className="mb-2">
            <span className="text-xs text-muted-foreground">Title:</span>
            <span className="ml-1 font-semibold">{result.title}</span>
          </div>
          <div className="mb-2">
            <span className="text-xs text-muted-foreground">Score:</span>
            <span className="ml-1">{result.score.toFixed(3)}</span>
          </div>
          <div className="mb-2">
            <span className="text-xs text-muted-foreground">Created:</span>
            <span className="ml-1">{new Date(result.created_at).toLocaleString()}</span>
          </div>
          <div className="mb-2">
            <span className="text-xs text-muted-foreground">Chunk:</span>
            <div className="mt-1 whitespace-pre-line text-sm line-clamp-4">{result.chunk_text}</div>
          </div>
          {result.document_text && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-muted-foreground">
                Full Document
              </summary>
              <div className="mt-1 whitespace-pre-line text-xs line-clamp-2">
                {result.document_text}
              </div>
            </details>
          )}
        </div>
      </DialogTrigger>
      <DialogContent className="h-[90%] !max-w-2xl overflow-auto">
        <DialogHeader className="">
          <DialogTitle>{result.title}</DialogTitle>
          <DialogDescription>
            Score: {result.score.toFixed(3)} | Created:{' '}
            {new Date(result.created_at).toLocaleString()}
          </DialogDescription>
        </DialogHeader>
        <div className="mb-4">
          <div className="text-xs text-muted-foreground mb-1">Chunk (Markdown):</div>
          <div className="prose prose-sm max-w-none whitespace-pre-line">
            <ReactMarkdown>{result.chunk_text}</ReactMarkdown>
          </div>
        </div>
        {result.document_text && (
          <div>
            <div className="text-xs text-muted-foreground mb-1">Full Document (Markdown):</div>
            <div className="prose prose-xs max-w-none whitespace-pre-line">
              <ReactMarkdown>{result.document_text}</ReactMarkdown>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default SearchResultCard;
