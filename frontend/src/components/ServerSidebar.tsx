import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Server, ChevronDown, ChevronRight } from "lucide-react";
import type { MCPServer } from "@/types";

interface ServerSidebarProps {
  servers: MCPServer[];
}

export function ServerSidebar({ servers }: ServerSidebarProps) {
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set());

  const toggleServer = (serverName: string) => {
    const newExpanded = new Set(expandedServers);
    if (newExpanded.has(serverName)) {
      newExpanded.delete(serverName);
    } else {
      newExpanded.add(serverName);
    }
    setExpandedServers(newExpanded);
  };

  return (
    <div className="w-80 border-r border-[var(--color-border)] bg-[var(--color-card)] h-screen flex flex-col">
      <div className="p-4 border-b border-[var(--color-border)]">
        <h2 className="text-lg font-semibold">MCP Servers</h2>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {servers.length === 0 ? (
            <div className="text-[var(--color-muted-foreground)] text-sm text-center py-8">
              No servers connected
            </div>
          ) : (
            servers.map((server) => (
              <Card key={server.name} className="bg-[var(--color-secondary)]">
                <CardHeader
                  className="pb-2 cursor-pointer"
                  onClick={() => toggleServer(server.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {expandedServers.has(server.name) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      <Server className="h-4 w-4" />
                      <CardTitle className="text-sm font-medium">
                        {server.name}
                      </CardTitle>
                    </div>
                    <div
                      className={`h-2 w-2 rounded-full ${
                        server.connected ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                  </div>
                </CardHeader>
                {expandedServers.has(server.name) && (
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      {server.tools.length === 0 ? (
                        <div className="text-xs text-muted-foreground">
                          No tools available
                        </div>
                      ) : (
                        server.tools.map((tool) => (
                          <Badge
                            key={tool.name}
                            variant="outline"
                            className="w-full justify-start text-xs"
                          >
                            {tool.name}
                          </Badge>
                        ))
                      )}
                    </div>
                  </CardContent>
                )}
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

