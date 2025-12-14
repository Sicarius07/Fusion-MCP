export interface Message {
  id: string;
  type: "user" | "thinking" | "tool_call" | "tool_result" | "assistant";
  content: string;
  metadata?: {
    tool_name?: string;
    server_name?: string;
    args?: any;
    result?: string;
    error?: string;
  };
  timestamp: Date;
}

export interface MCPServer {
  name: string;
  connected: boolean;
  tools: MCPTool[];
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: any;
}

