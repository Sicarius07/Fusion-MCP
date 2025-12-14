# MCP Client

A full-stack MCP (Model Context Protocol) client with React frontend and FastAPI backend.

## Features

- Connect to multiple MCP servers (Slack, GitHub, Jira, custom servers)
- Chat interface with streaming responses
- Real-time display of model thinking steps and tool calls
- Server sidebar showing connected servers and available tools
- Dark theme UI built with shadcn/ui

## Setup

### Backend

1. Install Python dependencies:
```bash
uv sync
```

2. Create `.env` file in the project root:
```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

3. Configure MCP servers in `mcp_config.json` (already set up with a filesystem example):
```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

4. Run the backend from the `api` directory:
```bash
cd api
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

### Frontend

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Access the app at `http://localhost:5173`

The frontend will connect to the backend WebSocket at `ws://localhost:8000/ws`

## Architecture

- **Backend**: FastAPI with WebSocket support for streaming
- **Frontend**: React + TypeScript + Vite + shadcn/ui
- **LLM**: OpenAI GPT-4o with function calling
- **MCP**: Model Context Protocol for tool integration

## Usage

1. Start the backend server
2. Start the frontend dev server
3. The app will automatically connect to MCP servers defined in `mcp_config.json`
4. Start chatting - the model will use available tools as needed
