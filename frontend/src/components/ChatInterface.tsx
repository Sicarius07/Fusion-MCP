import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Send, Loader2, Wrench, CheckCircle2, MessageSquare } from "lucide-react";
import type { Message } from "@/types";

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isStreaming: boolean;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isStreaming,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isStreaming) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  const getMessageIcon = (type: Message["type"]) => {
    switch (type) {
      case "tool_call":
        return <Wrench className="h-4 w-4 text-blue-400" />;
      case "tool_result":
        return <CheckCircle2 className="h-4 w-4 text-green-400" />;
      case "assistant":
        return <MessageSquare className="h-4 w-4 text-purple-400" />;
      default:
        return null;
    }
  };

  const getMessageStyle = (type: Message["type"]) => {
    switch (type) {
      case "user":
        return "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] ml-auto";
      case "thinking":
        return "bg-[var(--color-muted)] text-[var(--color-muted-foreground)] italic";
      case "tool_call":
        return "bg-blue-950/50 border border-blue-800";
      case "tool_result":
        return "bg-green-950/50 border border-green-800";
      case "assistant":
        return "bg-[var(--color-secondary)]";
      default:
        return "bg-[var(--color-secondary)]";
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[var(--color-background)]">
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center text-[var(--color-muted-foreground)] py-12">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with the MCP client</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.type !== "user" && (
                  <div className="flex-shrink-0 mt-1">
                    {getMessageIcon(message.type)}
                  </div>
                )}
                <Card
                  className={`max-w-[80%] p-3 ${getMessageStyle(message.type)}`}
                >
                  <div className="text-sm whitespace-pre-wrap break-words">
                    {message.type === "tool_call" && message.metadata?.tool_name && (
                      <div className="font-semibold mb-1 text-blue-300">
                        Tool: {message.metadata.tool_name}
                      </div>
                    )}
                    {message.type === "tool_result" && message.metadata?.tool_name && (
                      <div className="font-semibold mb-1 text-green-300">
                        Result from {message.metadata.tool_name}
                      </div>
                    )}
                    {message.content}
                  </div>
                  {message.metadata?.args && (
                    <details className="mt-2 text-xs opacity-75">
                      <summary className="cursor-pointer">Arguments</summary>
                      <pre className="mt-1 p-2 bg-black/20 rounded overflow-auto">
                        {JSON.stringify(message.metadata.args, null, 2)}
                      </pre>
                    </details>
                  )}
                </Card>
                {message.type === "user" && (
                  <div className="flex-shrink-0 mt-1">
                    <MessageSquare className="h-4 w-4 text-primary" />
                  </div>
                )}
              </div>
            ))
          )}
          {isStreaming && (
            <div className="flex gap-3 justify-start">
              <Loader2 className="h-4 w-4 mt-1 animate-spin text-[var(--color-muted-foreground)]" />
              <Card className="bg-[var(--color-muted)] p-3">
                <div className="text-sm text-[var(--color-muted-foreground)]">Thinking...</div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <div className="border-t border-[var(--color-border)] p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 bg-[var(--color-secondary)] border border-[var(--color-input)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)]"
            disabled={isStreaming}
          />
          <Button type="submit" disabled={isStreaming || !input.trim()}>
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

