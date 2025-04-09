# Qdrant Semantic Search MCP Server

This project implements a Model Context Protocol (MCP) server that provides semantic search functionality using Qdrant vector database. Built with TypeScript and Bun, it exposes a tool that can be used by LLM applications to perform semantic searches.

## Features

- MCP server implementation with TypeScript and Bun
- Semantic search tool for querying Qdrant vector database
- Express-based HTTP server with SSE for client connections
- Mock embedding generation (can be replaced with actual embedding models)

## Prerequisites

- [Bun](https://bun.sh/) runtime
- [Qdrant](https://qdrant.tech/) vector database (running locally or remote)

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd earth-mcp-bun

# Install dependencies
bun install
```

## Configuration

The server can be configured through environment variables:

- `PORT`: HTTP server port (default: 3000)
- `HOST`: HTTP server host (default: 0.0.0.0)
- `QDRANT_URL`: URL of Qdrant server (default: http://localhost:6333)
- `QDRANT_COLLECTION`: Name of Qdrant collection to search (default: my_collection)

## Running the Server

```bash
bun run index.ts
```

The server will start and listen for incoming connections on the configured port.

## API Endpoints

- `GET /sse`: Connect via Server-Sent Events to receive responses
- `POST /messages?sessionId=<sessionId>`: Send messages to the server for a specific session

## Using the Find Tool

The server exposes a `find` tool that performs semantic search in the Qdrant database. Example usage:

```json
{
  "name": "find",
  "parameters": {
    "query": "your search query here",
    "limit": 5
  }
}
```

Parameters:
- `query`: The search query text
- `limit`: (Optional) Maximum number of results to return (default: 10)

## Integration with LLM Applications

This server can be integrated with LLM applications that support the Model Context Protocol. The client can connect to the `/sse` endpoint and send messages to the `/messages` endpoint.

## Development

To add more tools or modify the existing implementation, edit the `index.ts` file.

### Replacing the Mock Embedding Generation

For production use, replace the `getEmbedding` function with an actual embedding model implementation:

```typescript
async function getEmbedding(text: string): Promise<number[]> {
  // Call your embedding model API here
  // Return the resulting vector
}
```

## License

MIT
