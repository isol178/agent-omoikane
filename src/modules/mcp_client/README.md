## MCP Client (`client.py`)

This project includes a client (`client.py`) for interacting with an MCP (Model Context Protocol) server. This client facilitates communication with Large Language Models (LLMs) via various providers (currently supporting Anthropic and OpenAI) and allows for the execution of tools exposed by the MCP server.

**Functionality**:

 - **Provider Agnostic**: The client is designed to be adaptable to different LLM providers. Configuration determines which provider (Anthropic or OpenAI) to use. Adding support for new providers requires minimal code changes.
 - **Configuration Driven**: The client reads its server connection details from a JSON configuration file (mcp_client_config.json). This allows for easy switching between different servers without modifying the client code.
 - **Tool Invocation**: The client dynamically invokes tools provided by the MCP server. The LLM's response dictates which tools are called and with what parameters. The client handles the communication with the server to execute these tools and receive their results.
 - **Interactive Chat Loop**: The client provides a simple command-line interface for interactive conversations with the LLM. Users can input queries, and the client manages the interaction with the LLM and any necessary tool calls.
 - **Error Handling**: The client incorporates error handling to gracefully manage issues such as network problems, server errors, and invalid LLM responses.
 - **Asynchronous Operations**: The client uses asynchronous programming to efficiently handle multiple operations concurrently, such as LLM calls and tool executions.

**Usage**:

1. **Configuration**: Create a `mcp_client_config.json` file in the same directory as `client.py` with the following structure:

```json 
{
  "mcpServers": {
    "<server_key>": {
      "command": "<path_to_server_executable>",
      "args": ["<server_arguments>"]
    }
  }
}
```

Replace `<server_key>` with a unique identifier for your server, `<path_to_server_executable>` with the path to your MCP server executable, and `<server_arguments>` with any necessary arguments for the server.

2. **Execution**: Run the client from your terminal:

```bash
python client.py <provider> <server_key>
```

Replace `<provider>` with either "anthropic" or "openai", and `<server_key>` with the key defined in your configuration file.

3. **Interaction**: The client will establish a connection to the server and enter an interactive chat loop. Type your queries and the client will send them to the LLM, handle any tool calls, and display the results. Type "quit" to exit.

Example `mcp_client_config.json`:

```json 
{
  "mcpServers": {
    "git": {
      "command": "uvx", // Or "path/to/your/mcp-server-git" or docker command
      "args": [
               "mcp-server-git",
               "--repository",
               "/path/to/your/git/repo"
          ] // Add other necessary arguments
    }
  }
}
```

This configuration specifies a server located at `/path/to/my/mcp_server` with no additional arguments. Remember to replace this with your actual server path and arguments.

This improved description provides a more general and reusable explanation of the client's functionality, making it applicable to various MCP servers beyond just `mcp-server-git`.