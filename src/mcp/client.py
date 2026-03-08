"""MCP client wrapper with proper async context management."""

import asyncio
import logging
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import Tool
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple


logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_mcp_session(server_params: Dict[str, Any]) -> AsyncIterator[Tuple[ClientSession, List[Tool]]]:
    """
    Create an MCP session with proper context management.

    This ensures all async contexts are properly managed in the same task scope.
    """
    stdio_cm = None
    session_cm = None
    session = None

    try:
        params = StdioServerParameters(
            command=server_params["command"],
            args=server_params.get("args", []),
            env=server_params.get("env")
        )

        # Create stdio client
        stdio_cm = stdio_client(params)
        read_stream, write_stream = await stdio_cm.__aenter__()

        # Create and enter session
        session_cm = ClientSession(read_stream, write_stream)
        session = await session_cm.__aenter__()
        await session.initialize()

        # List tools
        tools_response = await session.list_tools()
        tools = tools_response.tools

        yield session, tools

    finally:
        # Cleanup in reverse order
        if session_cm is not None:
            try:
                await session_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Error closing session: {e}")

        if stdio_cm is not None:
            try:
                await stdio_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Error closing stdio client: {e}")


class MCPClient:
    """
    Wrapper for MCP server connection and tool execution.

    This client manages the connection lifecycle and provides a simple
    interface for calling tools.
    """

    def __init__(self, server_params: Dict[str, Any]):
        """Initialize MCP client with server parameters."""
        self.server_params = server_params
        self._session_holder: Optional[Dict] = None
        self._connect_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._closing = False

    @property
    def session(self) -> Optional[ClientSession]:
        """Get the current session."""
        if self._session_holder:
            return self._session_holder.get("session")
        return None

    @property
    def tools(self) -> List[Tool]:
        """Get the list of available tools."""
        if self._session_holder:
            return self._session_holder.get("tools", [])
        return []

    async def connect(self):
        """Connect to MCP server and initialize session."""
        async with self._lock:
            if self._session_holder is not None:
                return  # Already connected

            if self._closing:
                raise RuntimeError("Client is closing")

            # Create a task that will hold the connection alive
            self._connect_task = asyncio.create_task(self._hold_connection())

            # Wait for the session to be ready
            await asyncio.sleep(0.01)  # Small delay to let task start
            while self._session_holder is None:
                await asyncio.sleep(0.01)

    async def _hold_connection(self):
        """Background task that holds the connection alive."""
        try:
            async with create_mcp_session(self.server_params) as (session, tools):
                self._session_holder = {"session": session, "tools": tools}

                # Keep this task alive until we're closing
                while not self._closing:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Connection holder error: {e}")
        finally:
            self._session_holder = None

    async def call_tool(self, name: str, arguments: Dict) -> str:
        """Execute a tool and return result text."""
        session = self.session
        if session is None:
            raise RuntimeError("Client not connected. Call connect() first.")

        result = await session.call_tool(name, arguments)
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return ""

    async def close(self):
        """Clean up connections."""
        async with self._lock:
            self._closing = True

            if self._connect_task is not None:
                self._connect_task.cancel()
                try:
                    await self._connect_task
                except asyncio.CancelledError:
                    pass
                self._connect_task = None

            self._session_holder = None
            self._closing = False
