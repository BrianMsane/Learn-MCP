from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from mcp_client import MCPClient
from models import QueryRequest, ToolCall, Message



class Settings(BaseSettings):
    server_script_path: str = "/Users/DELL/Desktop/mcp-tutorial/app/server.py"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MCPClient()

    try:
        connected = await client.connect_to_server(settings.server_script_path)
        if not connected:
            raise HTTPException(500, "Failed to connect to MCP server")

        app.state.client = client
        yield
    except Exception:
        pass
    finally:
        await client.cleanup()


app = FastAPI(title="MCP Client API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "The MCP client and server tutorial"}


@app.post('/query')
async def process_query(request: QueryRequest):
    """Process a query and return the response"""
    try:
        messages: list = await app.state.client.process_query(request.query)
        return {"messages": messages} 
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app)
