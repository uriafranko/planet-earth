import React, { useState, useEffect } from 'react';
import { Plus, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AppLayout from '@/components/layout/AppLayout';
import { useToast } from '@/hooks/use-toast';
import { managementApi, schemasApi } from '@/services/api';
import { Schema } from '@/types/models';
import LoadingSpinner from '@/components/LoadingSpinner';
import SchemaCard from '@/components/cards/SchemaCard';
import NoData from '@/components/NoData';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useNavigate } from 'react-router-dom';

const Schemas: React.FC = () => {
  const { toast } = useToast();
  const navigate = useNavigate();

  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [schemaFile, setSchemaFile] = useState<File | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [schemaToDelete, setSchemaToDelete] = useState<Schema | null>(null);
  const [reindexingSchemas, setReindexingSchemas] = useState<string[]>([]);

  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    setIsLoading(true);
    try {
      const response = await schemasApi.getSchemas();
      if (response.data) {
        setSchemas(response.data);
      } else if (response.error) {
        toast({
          title: 'Error',
          description: `Failed to load schemas: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error loading schemas:', error);
      toast({
        title: 'Error',
        description: 'An unexpected error occurred while loading schemas',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!schemaFile) {
      toast({
        title: 'Upload Error',
        description: 'Please select a file to upload',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    try {
      const response = await schemasApi.uploadSchema(schemaFile);
      if (response.data) {
        toast({
          title: 'Upload Successful',
          description: `Schema "${response.data.title}" has been uploaded successfully`,
        });
        setSchemas([...schemas, response.data]);
        setUploadDialogOpen(false);
        setSchemaFile(null);
      } else if (response.error) {
        toast({
          title: 'Upload Error',
          description: `Failed to upload schema: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error uploading schema:', error);
      toast({
        title: 'Upload Error',
        description: 'An unexpected error occurred during upload',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleReindex = async (schemaId: string) => {
    try {
      setReindexingSchemas((prev) => [...prev, schemaId]);
      const response = await managementApi.reindexVectorStore(schemaId);
      if (!response.error) {
        toast({
          title: 'Reindexing Started',
          description: 'Vector store reindexing has been initiated',
        });
      } else {
        throw new Error(response.error.message);
      }
    } catch (error) {
      console.error('Error reindexing schema:', error);
      toast({
        title: 'Reindex Error',
        description: 'Failed to initiate reindexing process',
        variant: 'destructive',
      });
    } finally {
      // After a delay, remove from reindexing state
      setTimeout(() => {
        setReindexingSchemas((prev) => prev.filter((id) => id !== schemaId));
      }, 2000);
    }
  };

  const handleDelete = async () => {
    if (!schemaToDelete) return;

    try {
      const response = await schemasApi.deleteSchema(schemaToDelete.id);
      if (!response.error) {
        toast({
          title: 'Schema Deleted',
          description: `Schema "${schemaToDelete.title}" has been deleted`,
        });
        setSchemas(schemas.filter((s) => s.id !== schemaToDelete.id));
      } else {
        toast({
          title: 'Delete Error',
          description: `Failed to delete schema: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error deleting schema:', error);
      toast({
        title: 'Delete Error',
        description: 'An unexpected error occurred while deleting',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setSchemaToDelete(null);
    }
  };

  const handleSchemaSelect = (schema: Schema) => {
    navigate(`/endpoints?schema=${schema.id}`);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">API Schemas</h1>
            <p className="text-muted-foreground">Manage your OpenAPI schema definitions</p>
          </div>
          <Button onClick={() => setUploadDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Schema
          </Button>
        </div>

        {isLoading ? (
          <div className="h-40 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : schemas.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {schemas.map((schema) => (
              <SchemaCard
                key={schema.id}
                schema={schema}
                onSelect={() => handleSchemaSelect(schema)}
                onDelete={() => {
                  setSchemaToDelete(schema);
                  setDeleteDialogOpen(true);
                }}
                onReindex={() => handleReindex(schema.id)}
                isReindexing={reindexingSchemas.includes(schema.id)}
              />
            ))}

            <div
              onClick={() => setUploadDialogOpen(true)}
              className="h-full min-h-[200px] border border-dashed rounded-md flex flex-col items-center justify-center p-6 cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <div className="h-12 w-12 rounded-full bg-muted/60 flex items-center justify-center mb-3">
                <Plus className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground font-medium">Upload Schema</p>
            </div>
          </div>
        ) : (
          <NoData
            title="No schemas found"
            description="Click the 'Upload Schema' button to add your first OpenAPI schema."
          />
        )}
      </div>

      {/* Upload Schema Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload OpenAPI Schema</DialogTitle>
            <DialogDescription>
              Upload a YAML or JSON file containing your OpenAPI 3.x specification.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="schema-file">Schema File</Label>
              <Input
                id="schema-file"
                type="file"
                accept=".json,.yaml,.yml"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSchemaFile(e.target.files[0]);
                  }
                }}
              />
              <p className="text-sm text-muted-foreground">Supported formats: .json, .yaml, .yml</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpload} disabled={!schemaFile || isUploading}>
              {isUploading ? (
                <LoadingSpinner size="sm" className="mr-2" />
              ) : (
                <Upload className="h-4 w-4 mr-2" />
              )}
              Upload
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Schema</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the schema "{schemaToDelete?.title}"? This action will
              also delete all associated endpoints and cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
};

export default Schemas;
