
import sys
import asyncio
import io
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from src.modules.mcp_client.client import MCPClient

# Test that valid providers initialize without error.
@pytest.mark.asyncio
async def test_constructor_valid_providers():
    # Test with "anthropic"
    client_anthropic = MCPClient(provider="anthropic")
    assert client_anthropic.provider == "anthropic"
    # Test with "openai"
    client_openai = MCPClient(provider="openai")
    assert client_openai.provider == "openai"

# Test that an unsupported provider raises a ValueError.
def test_constructor_invalid_provider():
    with pytest.raises(ValueError) as exc_info:
        MCPClient(provider="unsupported")
    assert "Unknown provider" in str(exc_info.value)

# Test connect_to_server with an invalid server key.
@pytest.mark.asyncio
async def test_connect_to_server_invalid_key(monkeypatch):
    # Prepare a dummy configuration that does not include the tested server key.
    dummy_config = {
        "mcpServers": {
            "dummy": {
                "command": "node",
                "args": [],
                "env": {}
            }
        }
    }
    dummy_config_json = json.dumps(dummy_config)
    
    # Monkey-patch the open function in the module where it's used.
    # The target open call is in the client.py, so we patch builtins.open.
    monkeypatch.setattr("builtins.open", lambda f, mode="r": io.StringIO(dummy_config_json))
    
    client = MCPClient(provider="anthropic")
    with pytest.raises(KeyError) as exc_info:
        await client.connect_to_server("nonexistent_key")
    assert "Server key 'nonexistent_key' not found" in str(exc_info.value)
    
    # Cleanup the client's asynchronous exit stack if needed.
    await client.cleanup()
    
# Additional test for asynchronous cleanup behavior.
@pytest.mark.asyncio
async def test_cleanup():
    client = MCPClient(provider="openai")
    # Since no real connection is established, cleanup should simply close the exit stack.
    await client.cleanup()
    # If cleanup completes without error, the test is successful.
    assert True

# Running the tests with asyncio event loop.
if __name__ == "__main__":
    asyncio.run(pytest.main())
