"""Module: client.py

Overview:
    This module implements the MCPClient class which provides functionality for
    connecting to an MCP server, processing queries via communication with large
    language models (LLMs) through providers such as Anthropic and OpenAI, and
    facilitating an interactive chat session with integrated tool invocation
    capabilities.

Features:
    - Reads server configuration from 'mcp_client_config.json'.
    - Connects to an MCP server and lists available tools.
    - Processes queries by interfacing with LLM APIs and handling dynamic tool calls.
    - Provides an interactive chat loop for user queries.
    - Ensures proper cleanup of asynchronous resources.

Usage Example:
    client = MCPClient(provider='anthropic')
    await client.connect_to_server("your_server_key")
    await client.chat_loop()
    await client.cleanup()

Module Version: 1.0.0
"""

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
    """A client for interacting with an MCP server and LLM providers.

    This client supports connections to MCP servers by reading configuration
    from a file, initializing client sessions, and communicating with LLMs from
    providers such as Anthropic and OpenAI. It also manages interactive chat
    sessions with dynamic tool invocation.

    Attributes:
        session (Optional[ClientSession]): The active client session.
        exit_stack (AsyncExitStack): Stack for managing asynchronous cleanup.
        provider (str): The LLM provider, "anthropic" or "openai".
        llm: The LLM instance corresponding to the specified provider.
    """

    def __init__(self, provider: str = "anthropic"):
        """Initializes the MCPClient.

        Args:
            provider (str): The LLM provider to use. Valid values are "anthropic"
                and "openai". Defaults to "anthropic".

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.provider: str = provider
        if self.provider == "anthropic":
            self.llm = Anthropic()
        elif self.provider == "openai":
            self.llm = OpenAI()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def connect_to_server(self, server_key: str):
        """Establishes a connection to an MCP server.

        This method reads server configuration from 'mcp_client_config.json',
        launches the server process, initializes the client session, and prints
        the list of available tools from the server.

        Args:
            server_key (str): The key identifying the server configuration in
                'mcp_client_config.json'.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            KeyError: If the server_key is not present in the configuration.
            shutil.Error: If the server command execution fails.
            Exception: For any errors encountered during connection or session
                initialization.
        """
        config_file_path = os.path.join(os.path.dirname(__file__),
                                        "mcp_client_config.json")
        with open(config_file_path, "r") as f:
            config = json.load(f)

        if server_key in config.get("mcpServers", {}):
            server_conf = config["mcpServers"][server_key]
            # command = shutil.which(server_conf.get("command", "node"))
            command = server_conf.get("command", "node")
            args = server_conf.get("args", [])
            env = server_conf.get("env")
        else:
            raise KeyError(f"Server key '{server_key}' not found in config file.")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Processes a user query using LLM APIs and tool invocations.

        The method constructs an initial message from the query, retrieves the
        available tools, initiates an LLM API call, and handles any subsequent tool
        calls until a final response is obtained.

        Args:
            query (str): The user's query to be processed.

        Returns:
            str: The final response after processing the query and tool calls.
        """
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = await self._get_available_tools(response)

        # Initial LLM API call
        response = await self._api_call(messages, available_tools)

        # Process the response and handle any tool calls
        final_text = await self._get_final_text(response, messages, available_tools)

        return final_text

    async def chat_loop(self):
        """Launches an interactive chat loop for the MCP client.

        Continuously prompts the user for queries and outputs the responses
        received from processing each query. The loop can be exited by typing
        'quit'.
        """
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Performs cleanup of asynchronous resources.

        Closes the asynchronous exit stack, effectively cleaning up the active
        client session and any other resources.
        """
        await self.exit_stack.aclose()

    async def _get_available_tools(self, response: ListToolsResult):
        """Retrieves and formats available tools from the server response.

        Depending on the provider (Anthropic or OpenAI), this method extracts the
        tool names, descriptions, and input schemas, and formats them into the
        structure expected by the respective LLM API.

        Args:
            response (ListToolsResult): The server response containing available tools.

        Returns:
            list[dict]: A list of dictionaries representing the available tools.

        Raises:
            ValueError: If an unknown provider is specified.
        """
        available_tools = []
        if self.provider == "anthropic":
            available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools
            ]
        elif self.provider == "openai":
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

    async def _api_call(self, messages: list[dict[str, str]],
                        available_tools: list[dict]):
        """Makes an API call to the LLM provider with the constructed messages.

        Depending on the provider, this method calls the appropriate LLM API with
        the messages and available tools.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries for the API.
            available_tools (list[dict]): List of formatted available tools.

        Returns:
            The response from the LLM API.

        Raises:
            ValueError: If an unknown provider is specified.
        """
        if self.provider == "anthropic":
            response = self.llm.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )
        elif self.provider == "openai":
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=available_tools,
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return response

    async def _get_final_text(self, response, messages, available_tools):
        """Processes LLM responses until a final text response is obtained.

        Determines which provider-specific final text processing method to use,
        based on the provider currently configured.

        Args:
            response: The initial response from the LLM API.
            messages (list): The conversation history including system and user
                messages.
            available_tools (list[dict]): The list of available tools.

        Returns:
            str: The final text response after processing tool calls.
        """
        if self.provider == "anthropic":
            return await self._get_final_text_claude(response, messages, available_tools)
        elif self.provider == "openai":
            return await self._get_final_text_openai(response, messages, available_tools)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _get_final_text_claude(self, response, messages, available_tools):
        """Processes final text response for the Anthropic provider.

        Iteratively handles LLM responses and dynamic tool calls until a complete text
        response is produced without pending tool calls.

        Args:
            response: The initial Anthropic LLM response.
            messages (list): Conversation history.
            available_tools (list[dict]): Formatted list of available tools.

        Returns:
            str: The consolidated final text response.
        """
        final_text = []
        assistant_message_content = []
        # Continue until a response without tool calls is received.
        for content in response.content:
            if content.type == "text":
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input

                # Execute the tool call and record the invocation.
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

                # Get the next LLM response.
                response = await self._api_call(messages, available_tools)
                final_text.append(response.content[0].text)

        return "\n\n".join(final_text)

    async def _get_final_text_openai(self, response, messages, available_tools):
        """Processes final text response for the OpenAI provider.

        Iteratively processes the response, executing tool calls embedded within
        the message until a final text response is achieved.

        Args:
            response: The initial OpenAI LLM response.
            messages (list): Conversation history.
            available_tools (list[dict]): Formatted available tools.

        Returns:
            str: The final text response after executing all tool calls.
        """
        final_text = []
        while True:
            message = response.choices[0].message
            if message.content:
                final_text.append(message.content)

            # Exit loop if there are no more tool calls.
            if not message.tool_calls:
                break

            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id

                # Execute tool call.
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = await self.session.call_tool(tool_name, tool_args)
                tool_result_contents = [
                    content.model_dump() for content in tool_result.content
                ]
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                messages.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_result_contents,
                })

            response = await self._api_call(messages, available_tools)

        return "\n\n".join(final_text)

async def main():
    """Entry point for the MCP client command-line interface.

    Expects two command-line arguments: the provider and the server_key.
    If insufficient arguments are provided, prints usage instructions.

    Example:
        $ python client.py anthropic my_server_key
    """
    import sys
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
