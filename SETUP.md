# Quick Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

## Backend Setup

1. **Install dependencies** (from project root):
   ```bash
   uv sync
   ```

2. **Create `.env` file** in the project root:
   ```bash
   echo "OPENAI_API_KEY=sk-your-openai-key" > .env
   ```

3. **Start the backend** (from api directory):
   ```bash
   cd api
   uvicorn main:app --reload
   ```
   
   Server will run on `http://localhost:8000`

## Frontend Setup

1. **Install dependencies** (from frontend directory):
   ```bash
   cd frontend
   npm install
   ```

2. **Start the dev server**:
   ```bash
   npm run dev
   ```
   
   App will be available at `http://localhost:5173`

## Configuration

### MCP Servers

Edit `mcp_config.json` to add/remove MCP servers:

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

## Troubleshooting

### Backend Issues

**ModuleNotFoundError: No module named 'fastapi'**
- Make sure you ran `uv sync` from the project root
- Make sure you're in the `.venv` or run with `uv run`

**OpenAI API Error**
- Check that your `.env` file exists in the project root
- Verify your OpenAI API key is valid

### Frontend Issues

**Tailwind CSS not working**
- Make sure `@tailwindcss/postcss` is installed
- Check that `postcss.config.js` uses `@tailwindcss/postcss`

**WebSocket connection failed**
- Make sure the backend is running on port 8000
- Check CORS settings if accessing from different origin

## Testing

Once both servers are running:

1. Open `http://localhost:5173` in your browser
2. You should see the sidebar showing connected MCP servers
3. Type a message in the chat to test the AI response
4. Try asking to use available tools (e.g., "list files in /tmp")

