import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { QdrantClient } from '@qdrant/js-client-rest';
import { z } from 'zod';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express, { type Request, type Response } from 'express';
import { pipeline } from '@huggingface/transformers';

// Create the MCP server instance
const server = new McpServer({
  name: 'Search Any API scheme.',
  version: '1.0.0',
});

// Configure Qdrant client
const qdrantClient = new QdrantClient({
  url: process.env.QDRANT_URL || 'http://localhost:6333',
  apiKey: process.env.QDRANT_API_KEY,
});

// Define the collection name for Qdrant
const COLLECTION_NAME = process.env.QDRANT_COLLECTION || 'my_collection';

// Add the semantic search tool
server.tool(
  'Find any API scheme',
  {
    query: z.string().describe('Search query for API scheme - e.g. "Slack - Search messages"'),
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
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                status: 'success',
                results: searchResults.map((result) => ({
                  id: result.id,
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
    // Initialize the feature-extraction pipeline with all-MiniLM-L6-v2 model
    const model = await pipeline('feature-extraction', 'sentence-transformers/all-MiniLM-L6-v2', {
      dtype: 'fp32', // Explicitly specify dtype to fix warning
    });

    // Get the embedding
    const result = await model(text, {
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
app.listen(port, host, () => {
  console.log(`MCP server is running at http://${host}:${port}`);
  console.log(`Connect to the SSE endpoint at http://${host}:${port}/sse`);
});
