import React, { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import AppLayout from '@/components/layout/AppLayout';
import { useToast } from '@/hooks/use-toast';
import { searchApi } from '@/services/api';
import { EndpointSearchResult, SearchQuery } from '@/types/models';
import LoadingSpinner from '@/components/LoadingSpinner';
import NoData from '@/components/NoData';
import { useNavigate } from 'react-router-dom';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import EndpointSearchResultCard from '@/components/cards/EndpointSearchResultCard';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

const Search: React.FC = () => {
  const { toast } = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<EndpointSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [filterMethod, setFilterMethod] = useState<string | null>(null);
  const [filterSchemaId, setFilterSchemaId] = useState<string | null>(null);
  const [includeDeprecated, setIncludeDeprecated] = useState(false);

  // Modal state
  const [selectedEndpoint, setSelectedEndpoint] = useState<EndpointSearchResult | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

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

    const query: SearchQuery = {
      q: searchTerm,
      top_k: 20,
      filter_method: filterMethod,
      filter_schema_id: filterSchemaId,
      include_deprecated: includeDeprecated,
    };

    try {
      const response = await searchApi.searchEndpoints(query);
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
      console.error('Error performing search:', error);
      toast({
        title: 'Search Error',
        description: 'An unexpected error occurred during search',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Open modal with selected endpoint
  const handleResultSelect = (result: EndpointSearchResult) => {
    setSelectedEndpoint(result);
    setModalOpen(true);
  };

  // Close modal handler
  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedEndpoint(null);
  };

  // Modal content for endpoint details
  const renderEndpointModal = () => {
    if (!selectedEndpoint) return null;
    return (
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedEndpoint.method} {selectedEndpoint.path}
            </DialogTitle>
            <DialogDescription>
              <div className="mt-2">
                <div>
                  <span className="font-medium">API:</span> {selectedEndpoint.schema_title}
                </div>
                <div>
                  <span className="font-medium">Version:</span> {selectedEndpoint.schema_version}
                </div>
                {selectedEndpoint.summary && (
                  <div className="mt-2">
                    <span className="font-medium">Summary:</span> {selectedEndpoint.summary}
                  </div>
                )}
              </div>
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <div className="font-semibold mb-1">Spec (JSON):</div>
            <div className="bg-muted p-2 rounded text-xs overflow-x-auto max-h-64">
              {selectedEndpoint.spec ? (
                <pre className="whitespace-pre-wrap break-all">
                  {JSON.stringify(selectedEndpoint.spec, null, 2)}
                </pre>
              ) : (
                <span className="text-muted-foreground">No spec available for this endpoint.</span>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={handleModalClose}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {renderEndpointModal()}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Semantic Search</h1>
          <p className="text-muted-foreground">Search for API endpoints using natural language</p>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Input
                placeholder="Search for endpoints, e.g., 'how to create a user'"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            </div>

            <div className="flex flex-col sm:flex-row gap-2">
              <Select
                value={filterMethod || 'none'}
                onValueChange={(value) => setFilterMethod(value === 'none' ? null : value)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Any Method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Any Method</SelectItem>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                  <SelectItem value="PATCH">PATCH</SelectItem>
                </SelectContent>
              </Select>

              <div className="flex items-center gap-2">
                <Switch
                  id="include-deprecated"
                  checked={includeDeprecated}
                  onCheckedChange={setIncludeDeprecated}
                />
                <Label htmlFor="include-deprecated">Include deprecated</Label>
              </div>
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
                <EndpointSearchResultCard
                  key={result.id}
                  result={result}
                  onSelect={() => handleResultSelect(result)}
                />
              ))}
            </div>
          ) : (
            hasSearched && (
              <NoData
                title="No results found"
                description={
                  filterMethod
                    ? `No ${filterMethod} endpoints found matching "${searchTerm}"`
                    : `No endpoints found matching "${searchTerm}"${
                        includeDeprecated ? ' (including deprecated)' : ''
                      }`
                }
                icon={<SearchIcon className="h-8 w-8 text-muted-foreground" />}
              />
            )
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default Search;
