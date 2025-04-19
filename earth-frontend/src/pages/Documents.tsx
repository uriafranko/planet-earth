import React, { useState, useEffect } from 'react';
import { Plus, Upload, Search as SearchIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AppLayout from '@/components/layout/AppLayout';
import { useToast } from '@/hooks/use-toast';
import { documentsApi } from '@/services/api';
import { Document, DocumentDetail, DocumentSearchResult } from '@/types/models';
import LoadingSpinner from '@/components/LoadingSpinner';
import DocumentCard from '@/components/cards/DocumentCard';
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
import ReactMarkdown from 'react-markdown';

const Documents: React.FC = () => {
  const { toast } = useToast();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [documentTitle, setDocumentTitle] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [selectedDocumentContent, setSelectedDocumentContent] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await documentsApi.listDocuments();
      if (response.data) {
        setDocuments(response.data);
      } else if (response.error) {
        toast({
          title: 'Error',
          description: `Failed to load documents: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An unexpected error occurred while loading documents',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!documentFile || !documentTitle) {
      toast({
        title: 'Upload Error',
        description: 'Please provide a title and select a file to upload',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    try {
      const response = await documentsApi.uploadDocument(documentFile, documentTitle);
      if (response.data) {
        toast({
          title: 'Upload Successful',
          description: `Document "${response.data.title}" has been uploaded successfully`,
        });
        setDocuments([...documents, response.data]);
        setUploadDialogOpen(false);
        setDocumentFile(null);
        setDocumentTitle('');
      } else if (response.error) {
        toast({
          title: 'Upload Error',
          description: `Failed to upload document: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Upload Error',
        description: 'An unexpected error occurred during upload',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!documentToDelete) return;

    try {
      const response = await documentsApi.deleteDocument(documentToDelete.id);
      if (!response.error) {
        toast({
          title: 'Document Deleted',
          description: `Document "${documentToDelete.title}" has been deleted`,
        });
        setDocuments(documents.filter((d) => d.id !== documentToDelete.id));
      } else {
        toast({
          title: 'Delete Error',
          description: `Failed to delete document: ${response.error.message}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Delete Error',
        description: 'An unexpected error occurred while deleting',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    }
  };

  const handleSelectDocument = async (doc: Document) => {
    setSelectedDocument(doc);
    setSelectedDocumentContent(null);
    try {
      const response = await documentsApi.getDocument(doc.id);
      const detail: DocumentDetail | undefined = response.data;
      if (detail && detail.text) {
        setSelectedDocumentContent(detail.text);
      } else {
        setSelectedDocumentContent('No content available.');
      }
    } catch (error) {
      setSelectedDocumentContent('Failed to load document content.');
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
    setSearchResults(null);
    try {
      const response = await documentsApi.searchDocuments({ query: searchQuery });
      if (response.data) {
        setSearchResults(response.data);
      } else if (response.error) {
        toast({
          title: 'Search Error',
          description: `Failed to search documents: ${response.error.message}`,
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
      setIsSearching(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="text-muted-foreground">Upload, manage, and search your documents</p>
          </div>
          <Button onClick={() => setUploadDialogOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 items-center">
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-xs"
          />
          <Button type="submit" disabled={isSearching}>
            <SearchIcon className="h-4 w-4 mr-2" />
            Search
          </Button>
        </form>

        {isLoading ? (
          <div className="h-40 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : searchResults ? (
          <div>
            <h2 className="text-lg font-semibold mb-2">Search Results</h2>
            {searchResults.length > 0 ? (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {searchResults.map((result) => (
                  <DocumentCard
                    key={result.document_id}
                    document={{
                      id: result.document_id,
                      title: result.title,
                      created_at: result.created_at,
                      file_type: '',
                      original_filename: undefined,
                    }}
                    onSelect={() => {
                      const doc = documents.find((d) => d.id === result.document_id);
                      if (doc) handleSelectDocument(doc);
                    }}
                    onDelete={() => {
                      const doc = documents.find((d) => d.id === result.document_id);
                      if (doc) {
                        setDocumentToDelete(doc);
                        setDeleteDialogOpen(true);
                      }
                    }}
                  />
                ))}
              </div>
            ) : (
              <NoData title="No results found" description="Try a different search query." />
            )}
          </div>
        ) : documents.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onSelect={() => handleSelectDocument(doc)}
                onDelete={() => {
                  setDocumentToDelete(doc);
                  setDeleteDialogOpen(true);
                }}
              />
            ))}
            <div
              onClick={() => setUploadDialogOpen(true)}
              className="h-full min-h-[200px] border border-dashed rounded-md flex flex-col items-center justify-center p-6 cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <div className="h-12 w-12 rounded-full bg-muted/60 flex items-center justify-center mb-3">
                <Plus className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground font-medium">Upload Document</p>
            </div>
          </div>
        ) : (
          <NoData
            title="No documents found"
            description="Click the 'Upload Document' button to add your first document."
          />
        )}

        {/* Upload Document Dialog */}
        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload Document</DialogTitle>
              <DialogDescription>
                Upload a file and provide a title for your document.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="document-title">Title</Label>
                <Input
                  id="document-title"
                  type="text"
                  value={documentTitle}
                  onChange={(e) => setDocumentTitle(e.target.value)}
                  placeholder="Document title"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="document-file">File</Label>
                <Input
                  id="document-file"
                  type="file"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setDocumentFile(e.target.files[0]);
                    }
                  }}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleUpload}
                disabled={!documentFile || !documentTitle || isUploading}
              >
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
              <AlertDialogTitle>Delete Document</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete the document "{documentToDelete?.title}"? This
                action cannot be undone.
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

        {/* Document Content Modal */}
        <Dialog open={!!selectedDocument} onOpenChange={() => setSelectedDocument(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedDocument?.title}</DialogTitle>
              <DialogDescription>{selectedDocument?.original_filename}</DialogDescription>
            </DialogHeader>
            <div className="prose max-w-none overflow-y-auto max-h-[60vh]">
              {selectedDocumentContent === null ? (
                <LoadingSpinner />
              ) : (
                <ReactMarkdown>{selectedDocumentContent}</ReactMarkdown>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedDocument(null)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppLayout>
  );
};

export default Documents;
