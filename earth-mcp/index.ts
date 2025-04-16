import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express, { type Request, type Response } from 'express';
import { pipeline, env } from '@huggingface/transformers';
import path from 'path';
import fs from 'fs';

// Drizzle ORM imports
import { db } from './db/client.js';
import { endpoints } from './db/schema.js';
import { cosineDistance, isNull, sql, gt, desc } from 'drizzle-orm';

const MODEL_ID = 'jinaai/jina-embeddings-v2-base-en';
const CACHE_DIR = path.join(process.cwd(), '.cache', 'huggingface');

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
  'Find any API endpoint documentation by service name and description.',
  {
    query: z
      .string()
      .describe(
        'Search query for API endpoint documentation - e.g. "Slack - Search messages in channels" or "GitHub - Create repository by name"'
      ),
    limit: z
      .number()
      .min(1)
      .max(30)
      .optional()
      .default(5)
      .describe('Maximum number of results to return - default: 5'),
  },
  async ({ query, limit }) => {
    try {
      // Generate embedding vector for the query
      const vector = await getEmbedding(query);
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
        // .where(
        //   and(
        //     isNull(endpoints.deleted_at),
        //     lte(cosineDistance(endpoints.embedding_vector, vector), 0.5)
        //   )
        // )
        .where(gt(similarity, 0.4))
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
