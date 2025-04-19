import React, { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import AppLayout from '@/components/layout/AppLayout';
import { useToast } from '@/hooks/use-toast';
import { documentsApi } from '@/services/api';
import { DocumentSearchResult } from '@/types/models';
import LoadingSpinner from '@/components/LoadingSpinner';
import NoData from '@/components/NoData';
import DocumentCard from '@/components/cards/DocumentCard';
import SearchResultCard from '@/components/cards/SearchResultCard';

const DocumentSearch: React.FC = () => {
  const { toast } = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (!searchTerm.trim()) {
      toast({
        title: 'Search Error',
        description: 'Please enter a search term',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    setHasSearched(true);

    try {
      const response = await documentsApi.searchDocuments({ query: searchTerm, top_k: 20 });
      if (response.data) {
        setSearchResults(response.data);
      } else if (response.error) {
        toast({
          title: 'Search Error',
          description: `Error during search: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Search Error',
        description: 'An unexpected error occurred during search',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Document Vector Search</h1>
          <p className="text-muted-foreground">
            Semantic search for document content using natural language
          </p>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Input
                placeholder="Search for documents, e.g., 'project requirements in markdown'"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <LoadingSpinner size="sm" className="mr-2" />
              ) : (
                <SearchIcon className="h-4 w-4 mr-2" />
              )}
              Search
            </Button>
          </div>
        </form>

        <div className="space-y-4">
          {isLoading ? (
            <div className="h-40 flex items-center justify-center">
              <LoadingSpinner />
            </div>
          ) : searchResults.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {searchResults.map((result) => (
                <SearchResultCard key={result.chunk_id} result={result} />
              ))}
            </div>
          ) : (
            hasSearched && (
              <NoData
                title="No results found"
                description={`No document chunks found matching "${searchTerm}"`}
                icon={<SearchIcon className="h-8 w-8 text-muted-foreground" />}
              />
            )
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default DocumentSearch;
