import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express, { type Request, type Response } from 'express';
import { pipeline, env } from '@huggingface/transformers';
import path from 'path';
import fs from 'fs';

// Drizzle ORM imports
import { v4 as uuidv4 } from 'uuid';
import { db } from './db/client.js';
import { endpoints, audits, auditResults, documents, documentChunks } from './db/schema.js';
import { cosineDistance, sql, gt, desc } from 'drizzle-orm';

const MODEL_ID = 'BAAI/bge-base-en-v1.5';
const CACHE_DIR = path.join(process.cwd(), '.cache', 'huggingface');
const EMBEDDING_INSTRUCTIONS = 'Represent this sentence for searching relevant passages: ';

// Ensure cache directory exists
if (!fs.existsSync(CACHE_DIR)) {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Set the cache directory for Hugging Face
env.cacheDir = CACHE_DIR;

// Create the MCP server instance
const server = new McpServer({
  name: 'Search Any API endpoint specification.',
  version: '0.0.1',
  description: 'Search For Any API service endpoint for documentation.',
});

// Declare the model variable globally
let embeddingModel: any = null;

// Initialize the embedding model at startup
async function initializeEmbeddingModel() {
  console.log('Initializing embedding model...');
  try {
    embeddingModel = await pipeline('feature-extraction', MODEL_ID, {
      dtype: 'fp32',
      revision: 'main',
      cache_dir: CACHE_DIR,
    });
    console.log('Embedding model loaded successfully');
  } catch (error) {
    console.error('Error loading embedding model:', error);
    if (error instanceof Error) {
      console.error(error.message);
      console.error(error.stack);
    }
    process.exit(1); // Exit if we can't load the model as it's critical
  }
}

// Add the semantic search tool
server.tool(
  'find_api_spec',
  'Find any API endpoint documentation by description. Search query for API endpoint documentation - e.g. "Search Slack messages" or "Create a github repository". This will return a list of API endpoints that match the description.',
  {
    api_description: z
      .string()
      .describe(
        'A brief description of the API endpoint goal to search for. For example, "Search Slack messages" or "Create a GitHub repository".'
      ),
    limit: z
      .number()
      .min(1)
      .max(30)
      .optional()
      .default(5)
      .describe('Maximum number of results to return - default: 5'),
  },
  async ({ api_description, limit }) => {
    try {
      // Generate embedding vector for the query
      const vector = await getEmbedding(EMBEDDING_INSTRUCTIONS + api_description);
      const similarity = sql<number>`1 - (${cosineDistance(endpoints.embedding_vector, vector)})`;
      // Perform similarity search using Drizzle ORM and pgvector
      const results = await db
        .select({
          id: endpoints.id,
          schema_id: endpoints.schema_id,
          path: endpoints.path,
          method: endpoints.method,
          operation_id: endpoints.operation_id,
          summary: endpoints.summary,
          description: endpoints.description,
          tags: endpoints.tags,
          spec: endpoints.spec,
          similarity: similarity,
        })
        .from(endpoints)
        .where(gt(similarity, 0.5))
        .orderBy(desc(similarity))
        .limit(limit);

      // Map results to EndpointSearchResult structure
      const mapped = results.map((endpoint: any) => ({
        id: String(endpoint.id),
        schema_id: String(endpoint.schema_id),
        path: endpoint.path,
        method: endpoint.method,
        operation_id: endpoint.operation_id,
        summary: endpoint.summary,
        description: endpoint.description,
        tags: endpoint.tags ? JSON.parse(endpoint.tags) : [],
        similarity: endpoint.similarity,
        spec: endpoint.spec ?? null,
      }));

      // --- AUDIT LOGGING ---
      let auditId: string | null = null;
      try {
        // Insert audit record
        const auditInsert = await db
          .insert(audits)
          .values({
            id: uuidv4(),
            query: api_description,
            total_result_count: mapped.length,
            created_at: new Date(),
          })
          .returning({ id: audits.id });
        auditId = auditInsert[0]?.id ?? null;
        // Insert auditResults for each endpoint
        if (typeof auditId === 'string') {
          const auditResultsToInsert = mapped.map((endpoint: any) => ({
            id: uuidv4(),
            created_at: new Date(),
            audit_id: String(auditId),
            schema_id: String(endpoint.schema_id),
            endpoint_id: String(endpoint.id),
            result_count: 1,
          })) as {
            id: string;
            created_at: Date;
            audit_id: string;
            schema_id: string;
            endpoint_id: string;
            result_count: number;
          }[];
          if (auditResultsToInsert.length > 0) {
            await db.insert(auditResults).values(auditResultsToInsert);
          }
        }
      } catch (auditErr) {
        console.error('Failed to save audit log:', auditErr);
      }
      // --- END AUDIT LOGGING ---

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                status: 'success',
                results: mapped,
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (err: unknown) {
      const error = err as Error;

      return {
        content: [
          {
            type: 'text',
            text: `Error during semantic search: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

/**
 * Semantic search for document chunks, joining parent document.
 */
server.tool(
  'search_documents',
  'Semantic search for document chunks, returning both chunk and parent document info.',
  {
    query: z.string().describe('The search query for document content.'),
    limit: z
      .number()
      .min(1)
      .max(30)
      .optional()
      .default(10)
      .describe('Maximum number of results to return - default: 10'),
  },
  async ({ query, limit }) => {
    try {
      // Generate embedding vector for the query
      const vector = await getEmbedding(EMBEDDING_INSTRUCTIONS + query);
      const similarity = sql<number>`1 - (${cosineDistance(documentChunks.embedding, vector)})`;

      // Join document_chunks with documents, search by embedding similarity
      const results = await db
        .select({
          document_id: documentChunks.document_id,
          chunk_id: documentChunks.id,
          title: documents.title,
          // chunk_text: documentChunks.text,
          document_text: documents.text,
          score: similarity,
          created_at: documentChunks.created_at,
        })
        .from(documentChunks)
        .innerJoin(documents, sql`${documentChunks.document_id} = ${documents.id}`)
        .where(gt(similarity, 0.5))
        .orderBy(desc(similarity))
        .limit(limit);

      // Map results to match DocumentSearchResult
      const mapped = results.map((row: any) => ({
        document_id: String(row.document_id),
        chunk_id: String(row.chunk_id),
        title: row.title,
        document_text: row.document_text,
        score: row.score,
        created_at: row.created_at,
      }));

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                status: 'success',
                results: mapped,
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (err: unknown) {
      const error = err as Error;
      return {
        content: [
          {
            type: 'text',
            text: `Error during document search: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// Helper function to get embeddings for the query using all-MiniLM-L6-v2
async function getEmbedding(text: string): Promise<number[]> {
  try {
    // Use the pre-loaded model instead of initializing it each time
    if (!embeddingModel) {
      throw new Error('Embedding model not initialized');
    }

    // Get the embedding
    const result = await embeddingModel(text, {
      pooling: 'mean',
      normalize: true,
    });

    // Convert the embedding tensor to a regular JavaScript array
    return Array.from(result.data);
  } catch (error) {
    console.error('Error generating embedding:', error);
    // Log more details about the error
    if (error instanceof Error) {
      console.error(error.message);
      console.error(error.stack);
    }
    throw new Error(
      `Failed to generate embedding: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

// Set up an Express app to serve the MCP server
const app = express();
const port = Number(process.env.PORT) || 3000;
const host = process.env.HOST || '0.0.0.0';

// Store active transports by session ID
const transports: { [sessionId: string]: SSEServerTransport } = {};

// SSE endpoint for client to connect
app.get('/sse', async (_: Request, res: Response) => {
  const transport = new SSEServerTransport('/messages', res);
  transports[transport.sessionId] = transport;

  res.on('close', () => {
    delete transports[transport.sessionId];
  });

  await server.connect(transport);
});

// Endpoint for client to send messages
app.post('/messages', async (req: Request, res: Response) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports[sessionId];

  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    res.status(400).send('No transport found for sessionId');
  }
});

// Start the Express server
app.listen(port, host, async () => {
  // Initialize the embedding model before accepting requests
  await initializeEmbeddingModel();

  console.log(`MCP server is running at http://${host}:${port}`);
  console.log(`Connect to the SSE endpoint at http://${host}:${port}/sse`);
});
