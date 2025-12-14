"""OpenAI Handler - Manages streaming chat with tool calling."""
import json
from typing import AsyncGenerator, Dict, Any, List
from openai import AsyncOpenAI
from mcp_manager import get_manager


class OpenAIHandler:
    """Handles OpenAI API calls with MCP tool integration."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.manager = get_manager()
    
    def _convert_mcp_tools_to_openai(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format."""
        all_tools = self.manager.get_all_tools()
        openai_tools = []
        
        for server_name, tools in all_tools.items():
            for tool in tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": f"{server_name}__{tool['name']}",
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {}),
                    }
                }
                openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def process_message(
        self, 
        conversation_history: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user message with streaming and tool calling."""
        # conversation_history should already include the user message
        messages = conversation_history.copy()
        
        mcp_tools = self._convert_mcp_tools_to_openai()
        
        # Main loop: continue until we get a final response
        while True:
            # Stream the completion
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=mcp_tools if mcp_tools else None,
                stream=True,
            )
            
            assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
            finish_reason = None
            current_tool_call = None
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason
                
                # Handle content
                if delta.content:
                    assistant_message["content"] += delta.content
                    yield {
                        "type": "assistant",
                        "content": delta.content,
                    }
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        
                        # Initialize tool call if needed
                        while len(assistant_message["tool_calls"]) <= index:
                            assistant_message["tool_calls"].append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        tool_call = assistant_message["tool_calls"][index]
                        
                        if tool_call_delta.id:
                            tool_call["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_call["function"]["name"] = tool_call_delta.function.name
                            
                            if tool_call_delta.function.arguments:
                                tool_call["function"]["arguments"] += tool_call_delta.function.arguments
                                
                                # Stream tool call info
                                if not current_tool_call or current_tool_call["name"] != tool_call["function"]["name"]:
                                    current_tool_call = {
                                        "name": tool_call["function"]["name"],
                                        "arguments": tool_call["function"]["arguments"]
                                    }
                                    yield {
                                        "type": "tool_call",
                                        "content": f"Calling tool: {tool_call['function']['name']}",
                                        "metadata": {
                                            "tool_name": tool_call["function"]["name"],
                                            "args": tool_call["function"]["arguments"]
                                        }
                                    }
            
            # Add assistant message to history
            messages.append(assistant_message)
            
            # If no tool calls, we're done
            if finish_reason != "tool_calls" or not assistant_message.get("tool_calls"):
                # Send completion signal
                yield {
                    "type": "complete",
                    "content": "",
                }
                break
            
            # Execute tool calls
            for tool_call in assistant_message["tool_calls"]:
                tool_name_full = tool_call["function"]["name"]
                tool_args_str = tool_call["function"]["arguments"]
                
                try:
                    # Parse tool name (format: server__tool)
                    if "__" not in tool_name_full:
                        raise ValueError(f"Invalid tool name format: {tool_name_full}")
                    
                    server_name, actual_tool_name = tool_name_full.split("__", 1)
                    tool_args = json.loads(tool_args_str)
                    
                    # Execute tool
                    yield {
                        "type": "tool_result",
                        "content": f"Executing {actual_tool_name} on {server_name}...",
                        "metadata": {
                            "tool_name": actual_tool_name,
                            "server_name": server_name,
                        }
                    }
                    
                    result = await self.manager.call_tool(server_name, actual_tool_name, tool_args)
                    
                    # Format result
                    result_text = "\n".join([
                        item.get("text", str(item))
                        for item in result.get("content", [])
                    ])
                    
                    if result.get("isError"):
                        result_text = f"Error: {result_text}"
                    
                    yield {
                        "type": "tool_result",
                        "content": f"Result from {actual_tool_name}: {result_text}",
                        "metadata": {
                            "tool_name": actual_tool_name,
                            "result": result_text,
                        }
                    }
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": result_text,
                        "tool_call_id": tool_call["id"],
                    })
                    
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name_full}: {str(e)}"
                    yield {
                        "type": "tool_result",
                        "content": error_msg,
                        "metadata": {"error": str(e)},
                    }
                    
                    messages.append({
                        "role": "tool",
                        "content": error_msg,
                        "tool_call_id": tool_call["id"],
                    })

