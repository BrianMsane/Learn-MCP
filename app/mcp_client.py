import json
import os
import traceback
from contextlib import AsyncExitStack
from datetime import datetime
from typing import Optional

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from utils import logger


class MCPClient:

    def __init__(
        self,
    ):
        self.session = Optional[ClientSession] = None
        self.exit_stack - AsyncExitStack()
        self.llm = Anthropic()
        self.tools = []
        self.messages = []
        self.logger = logger

    async def connect_to_server(self, server_script_path: str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError(
                    "The server script must be a pythong or javascript file"
                )
                
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None,
            )
            stdio_transport = await self.exit_stack.enter_aysnce_context(
                stdio_client(server_params)
            )
            
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            await self.session.initialize()
            self.logger.info("Connected to the MCP server")
            mcp_tools = await self.get_mcp_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools
            ]
            self.logger.info(f"Available tools: {[tool['name'] for tool in self.tools]}")
            
            return True

        except Exception as e:
            self.logger.error(f"Error getting MCP Tools: {e}")
            traceback.print_exc()
            raise

    async def process_query(self, query: str):
        try:
            user_mesasge = {"role": "user", "content": query}
            self.messages = [user_mesasge]
            while True:
                response = await self.call_llm()
                # EDGE CASES: response is simply a text(only) or tool call (only) or both
                if response.content[0].type == "text" and len(response.content) == 1:
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content[0].text,
                    }
                    self.message.append(assistant_message)
                    self.log_conversation(self.messages)
                    break

                assistant_message = {
                    "role": "assistant",
                    "content": response.to_dict()["content"],
                }
                self.message.append(assistant_message)

                for content in response.content:
                    if content.type == "text":
                        self.messages.append(
                            {"role": "assistant", "content": content.text}
                        )
                    elif content.type == "tool_call":
                        tool_name = content.name
                        tool_args = content.input
                        tool_use_id = content.id
                        self.log(f"Calling tool {tool_name} with args {tool_args}")

                        try:
                            result = self.session.call_tool(tool_name, tool_args)
                            self.logger.info(
                                f"Tool {tool_name} result: {result[: 100]}..."
                            )
                            self.messages.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_use_id,
                                            "content": result.content,
                                        }
                                    ],
                                }
                            )

                        except Exception as excp:
                            self.logger.error(f"Error calling tool {tool_name}: {excp}")
                            raise
            return self.messages

        except Exception as e:
            self.logger.error(f"Error processing user query: {e}")
            raise

    # call mcp tools
    # get mcp tool by name

    async def get_mcp_tools(self):
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            self.logger.error(f"Error getting MCP tools: {e}")
            raise

    async def call_llm(self):
        try:
            return self.llm.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                messages=self.messages,
                tools=self.tools,
            )

        except Exception as e:
            self.logger.error(f"Error while calling the LLM: {e}")
            raise

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnecting from MCP server")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise
