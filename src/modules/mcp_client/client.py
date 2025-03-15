import os
import shutil
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import json

from mcp import ClientSession, StdioServerParameters, ListToolsResult
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
     def __init__(self, provider='anthropic'):
          # Initialize session and client objects
          self.session: Optional[ClientSession] = None
          self.exit_stack = AsyncExitStack()
          self.provider: str = provider
          if self.provider == 'anthropic':
               self.llm = Anthropic()
          elif self.provider == 'openai':
               self.llm = OpenAI()
          else:
               raise ValueError(f"Unknown provider: {provider}")


     async def connect_to_server(self, server_key: str):
          """Connects to an MCP (Model Context Protocol) server.

          This method establishes a connection to a specified MCP server,
          reads its configuration from 'mcp_client_config.json',
          starts the server process, initializes a client session,
          and lists the available tools provided by the server.

          Args:
              server_key: The key of the server to connect to, as defined in
                  'mcp_client_config.json'.

          Raises:
              FileNotFoundError: If 'mcp_client_config.json' is not found.
              KeyError: If the provided `server_key` is not found in the config file.
              shutil.Error: If the command specified in the config file is not found.
              Exception: If any error occurs during the connection or initialization process.
          """
          config_file_path = os.path.join(os.path.dirname(__file__), "mcp_client_config.json")
          with open(config_file_path, "r") as f:
               config = json.load(f)

          if server_key in config.get("mcpServers", {}):
               server_conf = config["mcpServers"][server_key]
               # command = shutil.which(server_conf.get("command", "node"))
               command = server_conf.get("command")
               args = server_conf.get("args", [])
               env = server_conf.get("env")

          server_params = StdioServerParameters(
               command=command,
               args=args,
               env=env
          )

          stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
          self.stdio, self.write = stdio_transport
          self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

          await self.session.initialize()

          # List available tools
          response = await self.session.list_tools()
          tools = response.tools
          print("\nConnected to server with tools:", [tool.name for tool in tools])
     

     async def process_query(self, query: str) -> str:
          """Process a query using Claude and available tools"""
          messages = [
               {
                    "role": "user",
                    "content": query
               }
          ]

          response = await self.session.list_tools()
          available_tools = await self._get_available_tools(response)

          # Initial llm API call
          response = await self._api_call(messages, available_tools)

          # Process response and handle tool calls
          final_text = await self._get_final_text(response, messages, available_tools)

          return final_text
     

     async def chat_loop(self):
          """Run an interactive chat loop"""
          print("\nMCP Client Started!")
          print("Type your queries or 'quit' to exit.")

          while True:
               try:
                    query = input("\nQuery: ").strip()

                    if query.lower() == 'quit':
                         break

                    response = await self.process_query(query)
                    print("\n" + response)

               except Exception as e:
                    print(f"\nError: {str(e)}")


     async def cleanup(self):
          """Clean up resources"""
          await self.exit_stack.aclose()
     

     async def _get_available_tools(self, response: ListToolsResult):
          """Get available tools"""
          available_tools = []
          if self.provider == 'anthropic':
               available_tools = [
                    {
                         "name": tool.name,
                         "description": tool.description,
                         "input_schema": tool.inputSchema
                    } for tool in response.tools
               ]
          elif self.provider == 'openai':
               available_tools = [
                    {
                         "type": "function",
                         "function": {
                              "name": tool.name,
                              "description": tool.description,
                              "parameters": tool.inputSchema
                         }
                    } for tool in response.tools
               ]
          else:
               raise ValueError(f"Unknown provider: {self.provider}")
     
          return available_tools
     

     async def _api_call(self, messages: list[dict[str, str]], available_tools: list[dict]):
          if self.provider == 'anthropic':
               response = self.llm.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools
               )
          elif self.provider == 'openai':
               response = self.llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=available_tools,
               )
          else:
               raise ValueError(f"Unknown provider: {self.provider}")
          
          return response


     async def _get_final_text(self, response, messages, available_tools):
          if self.provider == 'anthropic':
               return await self._get_final_text_claude(response, messages, available_tools)
          elif self.provider == 'openai':
               return await self._get_final_text_openai(response, messages, available_tools)
          else:
               raise ValueError(f"Unknown provider: {self.provider}")


     async def _get_final_text_claude(self, response, messages, available_tools):
          # Process response and handle tool calls
          final_text = []
          assistant_message_content = []
          # This process continues until llm provides a final text response without requesting any more tool calls.
          for content in response.content:
               # If no tools were called, return it directly.
               if content.type == 'text':
                    final_text.append(content.text)
                    assistant_message_content.append(content)
               # If any tools were called, execute them and add their results to the messages.
               elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input

                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    assistant_message_content.append(content)
                    messages.append({
                         "role": "assistant",
                         "content": assistant_message_content
                    })
                    messages.append({
                         "role": "user",
                         "content": [
                              {
                              "type": "tool_result",
                              "tool_use_id": content.id,
                              "content": result.content
                              }
                         ]
                    })

                    # Get next response from llm
                    response = await self._api_call(messages, available_tools)

                    final_text.append(response.content[0].text)
          
          final_text = "\n\n".join(final_text)
          
          return final_text
     

     async def _get_final_text_openai(self, response, messages, available_tools):
          final_text = []
          # This process continues until llm provides a final text response without requesting any more tool calls.
          while True:
               message = response.choices[0].message
               if message.content:
                    final_text.append(message.content)
               
               # No more tool calls, exit the loop
               if not message.tool_calls:
                    break

               messages.append(message)

               # If any tools were called, execute them and add their results to the messages.
               for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_call_id = tool_call.id

                    # Execute tool call
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_result = await self.session.call_tool(tool_name, tool_args)
                    tool_result_contents = [content.model_dump() for content in tool_result.content]
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    messages.append(
                         {
                              "tool_call_id": tool_call_id,
                              "role": "tool",
                              "name": tool_name,
                              "content": tool_result_contents,
                         }
                    )

               response = await self._api_call(messages, available_tools)
          
          final_text = "\n\n".join(final_text)
          return final_text



async def main():
     if len(sys.argv) < 3:
          print("Usage: python client.py <provider> <server_key>")
          sys.exit(1)

     client = MCPClient(sys.argv[1])
     try:
          await client.connect_to_server(sys.argv[2])
          await client.chat_loop()
     finally:
          await client.cleanup()

if __name__ == "__main__":
     import sys
     asyncio.run(main())
