
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FileJson, Filter, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AppLayout from '@/components/layout/AppLayout';
import { useToast } from '@/hooks/use-toast';
import { endpointsApi, schemasApi } from '@/services/api';
import { Endpoint, Schema } from '@/types/models';
import LoadingSpinner from '@/components/LoadingSpinner';
import NoData from '@/components/NoData';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import EndpointCard from '@/components/cards/EndpointCard';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import MethodBadge from '@/components/MethodBadge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface EndpointDetailsProps {
  endpoint: Endpoint | null;
  onClose: () => void;
}

const EndpointDetails: React.FC<EndpointDetailsProps> = ({ endpoint, onClose }) => {
  if (!endpoint) return null;
  
  // Split tags string into array if exists
  const tags = endpoint.tags ? endpoint.tags.split(',').map(t => t.trim()) : [];
  
  return (
    <Dialog open={!!endpoint} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MethodBadge method={endpoint.method} size="lg" />
            <span className="font-mono">{endpoint.path}</span>
          </DialogTitle>
          <DialogDescription>
            {endpoint.operation_id && (
              <span className="block mt-2">
                <span className="font-semibold">Operation ID:</span> {endpoint.operation_id}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {endpoint.summary && (
            <div>
              <h3 className="text-sm font-semibold mb-1">Summary</h3>
              <p className="text-sm">{endpoint.summary}</p>
            </div>
          )}
          
          {endpoint.description && (
            <div>
              <h3 className="text-sm font-semibold mb-1">Description</h3>
              <p className="text-sm whitespace-pre-line">{endpoint.description}</p>
            </div>
          )}
          
          {tags.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-1">Tags</h3>
              <div className="flex flex-wrap gap-1">
                {tags.map((tag, index) => (
                  <Badge key={index} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          
          <div className="space-y-1">
            <h3 className="text-sm font-semibold">Metadata</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Created:</span>{' '}
                {new Date(endpoint.created_at).toLocaleString()}
              </div>
              {endpoint.deleted_at && (
                <div>
                  <span className="text-muted-foreground">Deleted:</span>{' '}
                  {new Date(endpoint.deleted_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const Endpoints: React.FC = () => {
  const { toast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get schema ID from URL query parameters
  const queryParams = new URLSearchParams(location.search);
  const schemaIdFromUrl = queryParams.get('schema');
  
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string | null>(schemaIdFromUrl);
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSchemas, setIsLoadingSchemas] = useState(true);
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [methodFilters, setMethodFilters] = useState<string[]>([]);
  
  // Load all schemas
  useEffect(() => {
    const loadSchemas = async () => {
      setIsLoadingSchemas(true);
      try {
        const response = await schemasApi.getSchemas();
        if (response.data) {
          setSchemas(response.data);
          
          // If no schema is selected and we have schemas, select the first one
          if (!selectedSchema && response.data.length > 0) {
            setSelectedSchema(response.data[0].id);
          }
        }
      } catch (error) {
        console.error('Error loading schemas:', error);
        toast({
          title: 'Error',
          description: 'Failed to load schema information',
          variant: 'destructive',
        });
      } finally {
        setIsLoadingSchemas(false);
      }
    };
    
    loadSchemas();
  }, [toast, selectedSchema]);
  
  // Load endpoints when selected schema changes
  useEffect(() => {
    const loadEndpoints = async () => {
      if (!selectedSchema) {
        setEndpoints([]);
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      try {
        const response = await endpointsApi.getEndpoints(selectedSchema, includeDeleted);
        if (response.data) {
          setEndpoints(response.data);
        }
      } catch (error) {
        console.error('Error loading endpoints:', error);
        toast({
          title: 'Error',
          description: 'Failed to load endpoints',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    loadEndpoints();
  }, [selectedSchema, includeDeleted, toast]);
  
  const handleSchemaChange = (schemaId: string) => {
    setSelectedSchema(schemaId);
    // Update URL query parameter
    navigate(`/endpoints?schema=${schemaId}`);
  };
  
  const handleIncludeDeletedChange = (checked: boolean) => {
    setIncludeDeleted(checked);
  };
  
  const toggleMethodFilter = (method: string) => {
    setMethodFilters((prev) => {
      if (prev.includes(method)) {
        return prev.filter((m) => m !== method);
      } else {
        return [...prev, method];
      }
    });
  };
  
  // Get unique HTTP methods from endpoints
  const availableMethods = [...new Set(endpoints.map((e) => e.method))];
  
  // Filter endpoints by method
  const filteredEndpoints = methodFilters.length
    ? endpoints.filter((endpoint) => methodFilters.includes(endpoint.method))
    : endpoints;

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">API Endpoints</h1>
            <p className="text-muted-foreground">
              View and manage API endpoints from your schemas
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <Select
              value={selectedSchema || ''}
              onValueChange={handleSchemaChange}
              disabled={isLoadingSchemas || schemas.length === 0}
            >
              <SelectTrigger className="min-w-[200px]">
                <SelectValue placeholder="Select a schema" />
              </SelectTrigger>
              <SelectContent>
                {schemas.map((schema) => (
                  <SelectItem key={schema.id} value={schema.id}>
                    <div className="flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      {schema.title}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="icon">
                    <Filter className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {availableMethods.map((method) => (
                    <DropdownMenuCheckboxItem
                      key={method}
                      checked={methodFilters.includes(method)}
                      onCheckedChange={() => toggleMethodFilter(method)}
                    >
                      <MethodBadge method={method} size="sm" className="mr-2" />
                      {method}
                    </DropdownMenuCheckboxItem>
                  ))}
                  {availableMethods.length === 0 && (
                    <div className="text-sm text-center py-2 text-muted-foreground">
                      No methods available
                    </div>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
              
              <Button
                variant="outline"
                size="icon"
                onClick={() => {
                  setIncludeDeleted(!includeDeleted);
                }}
                className={includeDeleted ? 'bg-muted' : ''}
              >
                <RefreshCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {methodFilters.length > 0 && (
              <div className="flex items-center gap-1 mr-2">
                <span className="text-sm text-muted-foreground">Filtered by:</span>
                <div className="flex flex-wrap gap-1">
                  {methodFilters.map((method) => (
                    <Badge
                      key={method}
                      variant="secondary"
                      className="flex items-center gap-1"
                      onClick={() => toggleMethodFilter(method)}
                    >
                      {method}
                      <span className="cursor-pointer">×</span>
                    </Badge>
                  ))}
                  {methodFilters.length > 0 && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-xs"
                      onClick={() => setMethodFilters([])}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Label htmlFor="include-deleted" className="text-sm">
              Include deleted
            </Label>
            <Switch
              id="include-deleted"
              checked={includeDeleted}
              onCheckedChange={handleIncludeDeletedChange}
            />
          </div>
        </div>

        {isLoading ? (
          <div className="h-40 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : filteredEndpoints.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredEndpoints.map((endpoint) => (
              <EndpointCard
                key={endpoint.id}
                endpoint={endpoint}
                onViewDetails={() => setSelectedEndpoint(endpoint)}
              />
            ))}
          </div>
        ) : (
          <NoData
            title={
              selectedSchema
                ? 'No endpoints found'
                : 'No schema selected'
            }
            description={
              selectedSchema
                ? includeDeleted
                  ? 'There are no endpoints defined in this schema.'
                  : 'No active endpoints found. Try including deleted endpoints.'
                : 'Select a schema to view its endpoints.'
            }
          />
        )}
      </div>

      <EndpointDetails
        endpoint={selectedEndpoint}
        onClose={() => setSelectedEndpoint(null)}
      />
    </AppLayout>
  );
};

export default Endpoints;
