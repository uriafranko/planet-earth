import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { QdrantClient } from '@qdrant/js-client-rest';
import { z } from 'zod';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express, { type Request, type Response } from 'express';
import { pipeline, env } from '@huggingface/transformers';
import path from 'path';
import fs from 'fs';

// Configure Hugging Face to cache models locally
const MODEL_ID = 'sentence-transformers/all-MiniLM-L6-v2';
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

// Configure Qdrant client
const qdrantClient = new QdrantClient({
  url: process.env.QDRANT_URL || 'http://localhost:6333',
  apiKey: process.env.QDRANT_API_KEY,
});

// Define the collection name for Qdrant
const COLLECTION_NAME = process.env.QDRANT_COLLECTION || 'my_collection';

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

      // Search in Qdrant collection
      const searchResults = await qdrantClient.search(COLLECTION_NAME, {
        vector: vector,
        limit: limit,
        with_payload: true,
        score_threshold: 0.5,
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                status: 'success',
                results: searchResults.map((result) => ({
                  score: result.score,
                  payload: result.payload,
                })),
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
  console.log(`Generating embedding for: ${text}`);

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
