import { useState, useEffect, useRef } from "react";
import { ChatInterface } from "@/components/ChatInterface";
import { ServerSidebar } from "@/components/ServerSidebar";
import type { Message, MCPServer } from "@/types";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageRef = useRef<Message | null>(null);

  useEffect(() => {
    // Fetch servers on mount
    fetchServers();

    // Connect WebSocket
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "error") {
        addMessage({
          id: Date.now().toString(),
          type: "assistant",
          content: `Error: ${data.content}`,
          timestamp: new Date(),
        });
        setIsStreaming(false);
        currentMessageRef.current = null;
        return;
      }

      if (data.type === "complete") {
        setIsStreaming(false);
        currentMessageRef.current = null;
        return;
      }

      if (data.type === "assistant") {
        // Streaming content
        if (!currentMessageRef.current) {
          currentMessageRef.current = {
            id: Date.now().toString(),
            type: "assistant",
            content: data.content,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, currentMessageRef.current!]);
        } else {
          currentMessageRef.current.content += data.content;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { ...currentMessageRef.current! };
            return updated;
          });
        }
        setIsStreaming(true);
      } else if (data.type === "tool_call") {
        // Tool call
        const message: Message = {
          id: Date.now().toString(),
          type: "tool_call",
          content: data.content,
          metadata: data.metadata,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, message]);
        setIsStreaming(true);
      } else if (data.type === "tool_result") {
        // Tool result
        const message: Message = {
          id: Date.now().toString(),
          type: "tool_result",
          content: data.content,
          metadata: data.metadata,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, message]);
        setIsStreaming(true);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsStreaming(false);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsStreaming(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const fetchServers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/servers`);
      const data = await response.json();
      setServers(data.servers || []);
    } catch (error) {
      console.error("Error fetching servers:", error);
    }
  };

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const handleSendMessage = (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // Reset current message
    currentMessageRef.current = null;
    setIsStreaming(true);

    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "message",
          content,
        })
      );
    } else {
      console.error("WebSocket not connected");
      setIsStreaming(false);
    }
  };


  return (
    <div className="flex h-screen bg-[var(--color-background)] text-[var(--color-foreground)]">
      <ServerSidebar servers={servers} />
      <div className="flex-1">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}

export default App;
